plugins { id("com.android.application"); kotlin("android") }
android { namespace="com.roadtelemetry"; compileSdk=34; defaultConfig { applicationId="com.roadtelemetry"; minSdk=26; targetSdk=34 } }
dependencies { implementation("androidx.core:core-ktx:1.13.1") }
android { compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 } }
kotlin { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) } }
