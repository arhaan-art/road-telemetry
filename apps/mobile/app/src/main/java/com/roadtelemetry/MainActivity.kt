package com.roadtelemetry
import android.Manifest
import android.app.Activity
import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle
import android.os.SystemClock
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

/** Collects accel+gyro+GPS, buffers JSON to filesDir/queue.jsonl (offline), uploads when possible.
 *  Background use requires starting SensorService as a foreground service with a visible notification — explicit user toggle only. */
class MainActivity : Activity(), SensorEventListener, LocationListener {
    private lateinit var sensors: SensorManager
    private var lastLocation: Location? = null
    private val buffer = JSONArray()
    @Volatile private var collecting = false
    override fun onCreate(s: Bundle?) {
        super.onCreate(s)
        requestPermissions(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.CAMERA), 1)
        sensors = getSystemService(Context.SENSOR_SERVICE) as SensorManager
    }
    fun startCollecting() {
        collecting = true
        val lm = getSystemService(Context.LOCATION_SERVICE) as LocationManager
        try { lm.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000L, 2f, this) } catch (_: SecurityException) {}
        sensors.registerListener(this, sensors.getDefaultSensor(Sensor.TYPE_ACCELEROMETER), SensorManager.SENSOR_DELAY_GAME)
        sensors.registerListener(this, sensors.getDefaultSensor(Sensor.TYPE_GYROSCOPE), SensorManager.SENSOR_DELAY_GAME)
    }
    fun stopCollecting() { collecting = false; sensors.unregisterListener(this); flushToDisk() }
    override fun onLocationChanged(l: Location) { lastLocation = l }
    override fun onAccuracyChanged(s: Sensor?, a: Int) {}
    override fun onSensorChanged(e: SensorEvent) {
        if (!collecting) return
        val loc = lastLocation ?: return
        buffer.put(JSONObject().put("t_nanos", e.timestamp).put("mono_ms", SystemClock.elapsedRealtime())
            .put("sensor", e.sensor.type).put("x", e.values[0].toDouble()).put("y", e.values[1].toDouble()).put("z", e.values[2].toDouble())
            .put("lat", loc.latitude).put("lon", loc.longitude).put("speed", loc.speed.toDouble()).put("gps_time", loc.time))
        if (buffer.length() >= 250) flushToDisk()
    }
    private fun flushToDisk() { File(filesDir, "queue.jsonl").appendText(buffer.toString() + "\n"); buffer.clear() }
    fun upload(baseUrl: String, token: String) = thread {
        val f = File(filesDir, "queue.jsonl"); if (!f.exists()) return@thread
        val c = URL("$baseUrl/api/telemetry/ingest").openConnection() as HttpURLConnection
        c.requestMethod = "POST"; c.setRequestProperty("Authorization", "Bearer $token"); c.doOutput = true
        // Server schema mapping is done in TelemetryClient in production; 5xx keeps the file for retry, 2xx clears it.
        try { c.outputStream.use { it.write(f.readBytes()) }; if (c.responseCode in 200..299) f.delete() } catch (_: Exception) { /* retry next launch */ }
    }
}
