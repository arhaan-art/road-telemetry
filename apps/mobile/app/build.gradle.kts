plugins { id("com.android.application"); kotlin("android") }
android { namespace="com.roadtelemetry"; compileSdk=34; defaultConfig { applicationId="com.roadtelemetry"; minSdk=26; targetSdk=34 } }
dependencies { implementation("androidx.core:core-ktx:1.13.1") }
