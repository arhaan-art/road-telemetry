# Android app
Real Gradle project (Kotlin). SensorService collects accelerometer+gyroscope+GPS with elapsedRealtime timestamps, buffers to a local file queue, uploads via TelemetryClient when network returns. Build: open in Android Studio (Gradle wrapper sync downloads AGP) or `gradle assembleDebug` with Android SDK. Not built in CI (no emulator/device in this environment) — stated honestly.
