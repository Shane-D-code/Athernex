# Quick Guide: Open in Android Studio

## 🚀 Super Quick (3 Steps)

### 1. Open Android Studio
Launch Android Studio from your Start menu or desktop

### 2. Open Project
Click **"Open"** → Navigate to:
```
C:\Users\Admin\Desktop\mlpart\Athernex\VyapaarSetuAITester
```
Click **"OK"**

### 3. Wait for Gradle Sync
Wait 2-5 minutes for first-time setup (downloads dependencies)

**Done!** ✅

---

## 📱 Run the App (After Opening)

### On Emulator:
1. Click green **Run** button (▶️) at top
2. Select emulator
3. Wait for app to launch

### On Phone:
1. Enable USB Debugging on your phone
2. Connect phone via USB
3. Click green **Run** button (▶️)
4. Select your phone
5. Wait for app to install

---

## ⚠️ If You Get Errors

### "SDK location not found"
**Fix:**
1. File → Settings → System Settings → Android SDK
2. Note the SDK path
3. Create file `local.properties` with:
   ```
   sdk.dir=C\:\\Users\\YourUsername\\AppData\\Local\\Android\\Sdk
   ```

### "Gradle sync failed"
**Fix:**
1. Check internet connection
2. File → Invalidate Caches → Invalidate and Restart
3. Try opening again

### "Build failed"
**Fix:**
1. Build → Clean Project
2. Build → Rebuild Project

### "No run configuration" / Can't see Run button
**Fix:**
1. File → Sync Project with Gradle Files
2. Wait for sync to complete
3. If still not working, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

📖 **Complete troubleshooting guide**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 📂 Project Location

```
C:\Users\Admin\Desktop\mlpart\Athernex\VyapaarSetuAITester
```

**Important:** Open the `VyapaarSetuAITester` folder, NOT the parent `Athernex` folder!

---

## ✅ What You'll See

After the app launches, you'll see a welcome screen with:
- "VyapaarSetu AI Tester" title
- Foundation status
- Next steps

This confirms the app is working!

---

## 📖 Detailed Guide

For more details, see: [ANDROID_STUDIO_SETUP.md](ANDROID_STUDIO_SETUP.md)

---

**Need help?** Check the troubleshooting section in ANDROID_STUDIO_SETUP.md
