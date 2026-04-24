# ⚡ Speed Up Gradle Build

Gradle builds taking too long? Here are proven optimizations to make it faster.

---

## 🚀 Quick Fixes (Apply These First)

### 1. Enable Gradle Daemon & Parallel Builds

Create/edit `gradle.properties` in project root:

```properties
# Enable Gradle Daemon (keeps Gradle running in background)
org.gradle.daemon=true

# Enable parallel builds
org.gradle.parallel=true

# Increase memory allocation
org.gradle.jvmargs=-Xmx4096m -XX:MaxMetaspaceSize=512m -XX:+HeapDumpOnOutOfMemoryError

# Enable configuration cache (Gradle 8.0+)
org.gradle.configuration-cache=true

# Enable build cache
org.gradle.caching=true

# Use AndroidX
android.useAndroidX=true

# Enable R8 (faster than ProGuard)
android.enableR8.fullMode=true

# Disable unnecessary features
android.enableJetifier=false
android.nonTransitiveRClass=true
android.nonFinalResIds=true
```

### 2. Use Offline Mode (When Dependencies Are Downloaded)

In Android Studio:
- File → Settings → Build, Execution, Deployment → Gradle
- Check "Offline work"

Or command line:
```bash
.\gradlew.bat assembleDebug --offline
```

### 3. Disable Unnecessary Build Variants

In `app/build.gradle.kts`:
```kotlin
android {
    // Only build debug variant during development
    variantFilter {
        if (name == "release") {
            ignore = true
        }
    }
}
```

---

## 🔧 Medium Optimizations

### 4. Reduce Dependency Resolution Time

Add to `settings.gradle.kts`:
```kotlin
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        // Remove jcenter() if present (deprecated)
    }
}
```

### 5. Use Build Scan to Identify Bottlenecks

```bash
.\gradlew.bat assembleDebug --scan
```

This generates a detailed report showing what's taking time.

### 6. Exclude Unnecessary Resources

In `app/build.gradle.kts`:
```kotlin
android {
    defaultConfig {
        // Only include English resources during development
        resourceConfigurations += listOf("en")
        
        // Only include specific densities
        vectorDrawables.useSupportLibrary = true
    }
}
```

---

## 💪 Advanced Optimizations

### 7. Use Gradle Build Cache

Create `~/.gradle/gradle.properties`:
```properties
org.gradle.caching=true
org.gradle.caching.debug=false
```

### 8. Increase File Watcher Limit (Linux/Mac)

```bash
# Linux
echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Mac
# Usually not needed
```

### 9. Use SSD for Project & Gradle Cache

Move project and Gradle cache to SSD if on HDD:
- Project: Already on SSD (C: drive)
- Gradle cache: `C:\Users\Admin\.gradle\`

### 10. Disable Antivirus Scanning for Project Folders

Add these to antivirus exclusions:
- `C:\Users\Admin\Desktop\mlpart\Athernex\`
- `C:\Users\Admin\.gradle\`
- `C:\Users\Admin\.android\`

---

## 📊 Typical Build Times

| Optimization Level | First Build | Incremental Build |
|-------------------|-------------|-------------------|
| No optimization | 2-5 min | 30-60 sec |
| Quick fixes | 1-2 min | 15-30 sec |
| All optimizations | 30-60 sec | 5-15 sec |

---

## 🎯 What's Slowing You Down?

### Check Current Settings

```bash
# Check Gradle daemon status
.\gradlew.bat --status

# Check build with profiling
.\gradlew.bat assembleDebug --profile

# Check with build scan
.\gradlew.bat assembleDebug --scan
```

### Common Culprits

1. **First-time dependency download** (normal, happens once)
2. **No Gradle daemon** (starts new JVM each time)
3. **Low memory allocation** (default is too small)
4. **Antivirus scanning** (scans every file change)
5. **HDD instead of SSD** (slow disk I/O)
6. **Too many dependencies** (more to download/process)

---

## 🚀 Immediate Actions

Run these commands now:

```bash
cd VyapaarSetuAITester

# Stop all Gradle daemons
.\gradlew.bat --stop

# Clean build cache
.\gradlew.bat clean

# Build with optimizations
.\gradlew.bat assembleDebug --parallel --build-cache
```

---

## 📝 Recommended gradle.properties

Save this as `gradle.properties` in project root:

```properties
# Gradle Performance Optimizations
org.gradle.daemon=true
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.configureondemand=true
org.gradle.jvmargs=-Xmx4096m -XX:MaxMetaspaceSize=512m -XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8

# Android Optimizations
android.useAndroidX=true
android.enableJetifier=false
android.nonTransitiveRClass=true
android.nonFinalResIds=true
android.enableR8.fullMode=true

# Kotlin Optimizations
kotlin.incremental=true
kotlin.incremental.java=true
kotlin.incremental.js=true
kotlin.caching.enabled=true
kotlin.parallel.tasks.in.project=true

# Build Cache
org.gradle.unsafe.configuration-cache=true
org.gradle.unsafe.configuration-cache-problems=warn
```

---

## 🔍 Debugging Slow Builds

### Generate Build Report

```bash
.\gradlew.bat assembleDebug --profile --offline --build-cache
```

Check: `build/reports/profile/profile-*.html`

### Check What's Taking Time

```bash
# Verbose output
.\gradlew.bat assembleDebug --info

# Debug output (very verbose)
.\gradlew.bat assembleDebug --debug
```

---

## ⚡ Expected Results

After applying optimizations:

### First Build (Cold Start)
- **Before**: 2-5 minutes
- **After**: 30-90 seconds

### Incremental Build (Small Changes)
- **Before**: 30-60 seconds
- **After**: 5-15 seconds

### Gradle Sync in Android Studio
- **Before**: 30-60 seconds
- **After**: 5-15 seconds

---

## 🎯 Quick Checklist

Apply these in order:

- [ ] Create `gradle.properties` with optimizations
- [ ] Stop and restart Gradle daemon
- [ ] Enable offline mode (after first build)
- [ ] Add project folders to antivirus exclusions
- [ ] Use `--parallel` and `--build-cache` flags
- [ ] Disable release variant during development
- [ ] Run `--scan` to identify bottlenecks
- [ ] Increase JVM heap size if needed

---

## 💡 Pro Tips

1. **Use Offline Mode**: After first build, enable offline mode in Android Studio
2. **Avoid Clean Builds**: Only clean when necessary (dependency changes)
3. **Use Incremental Builds**: Make small changes and build frequently
4. **Keep Gradle Updated**: Newer versions are faster
5. **Use Build Cache**: Shares build outputs across projects
6. **Disable Unused Plugins**: Remove plugins you don't need

---

## 🚨 If Still Slow

### Check System Resources

```bash
# Check RAM usage
tasklist /FI "IMAGENAME eq java.exe"

# Check disk space
wmic logicaldisk get size,freespace,caption
```

### Nuclear Option (Last Resort)

```bash
# Delete all Gradle caches
rmdir /s /q %USERPROFILE%\.gradle\caches
rmdir /s /q %USERPROFILE%\.android\build-cache

# Delete project build folders
cd VyapaarSetuAITester
.\gradlew.bat clean
rmdir /s /q .gradle
rmdir /s /q app\build

# Rebuild from scratch
.\gradlew.bat assembleDebug --refresh-dependencies
```

---

## 📞 Quick Commands

```bash
# Fast incremental build
.\gradlew.bat assembleDebug --parallel --build-cache --offline

# Check what's slow
.\gradlew.bat assembleDebug --scan

# Stop all daemons
.\gradlew.bat --stop

# Clean and rebuild
.\gradlew.bat clean assembleDebug --parallel
```

---

**Apply the quick fixes first, then test your build speed!** ⚡
