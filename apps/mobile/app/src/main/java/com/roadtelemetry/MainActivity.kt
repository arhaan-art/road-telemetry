package com.roadtelemetry
// Android skeleton (Kotlin): collects GPS + accelerometer/gyroscope, buffers samples,
// POSTs to /api/telemetry/ingest. Requires Android Studio + device permissions to run.
// Permissions: ACCESS_FINE_LOCATION, CAMERA, BODY_SENSORS not needed. Background collection
// must use a foreground service with user-visible notification and explicit consent toggle.
import android.app.Activity
import android.hardware.SensorManager
import android.os.Bundle
class MainActivity : Activity() {
    override fun onCreate(s: Bundle?) { super.onCreate(s) }
    // SensorCollector: register SensorManager listeners (ACCELEROMETER, GYROSCOPE) at 50Hz,
    // tag each sample with GPS lat/lon + elapsedRealtimeNanos, flush every 10s via TelemetryClient.
}
