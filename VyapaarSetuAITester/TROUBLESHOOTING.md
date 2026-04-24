# Troubleshooting: Android Studio Not Recognizing App

## Problem: No Run Configuration / Can't Run App

If Android Studio doesn't show the green Run button or says "No configurations available", follow these steps:

---

## Solution 1: Sync Gradle (Most Common Fix)

### Step 1: Sync Project
1. Click **File → Sync Project with Gradle Files**
2. Wait for sync to complete (watch bottom status bar)
3. Look for "Gradle sync finished" message

### Step 2: Check for Errors
- If sync fails, check the "Build" tab at bottom
- Read error messages carefully
- Common issues:
  - Internet connection needed (downloads dependencies)
  - SDK not configured
  - Gradle version mismatch

### Step 3: Retry
After fixing errors:
1. **File → Invalidate Caches → Invalidate and Restart**
2. Wait for Android Studio to restart
3. Project should sync automatically

---

## Solution 2: Configure SDK Location

### Check SDK Path
1. Go to **File → Settings** (or Ctrl+Alt+S)
2. Navigate to **Appearance & Behavior → System Settings → Android SDK**
3. Note the "Android SDK Location" path

### Create local.properties
1. In the project root (`VyapaarSetuAITester/`), create file: `local.properties`
2. Add this line (replace with your actual SDK path):
   ```properties
   sdk.dir=C\:\\Users\\YourUsername\\AppData\\Local\\Android\\Sdk
   ```
   
   **Windows Example:**
   ```properties
   sdk.dir=C\:\\Users\\Admin\\AppData\\Local\\Android\\Sdk
   ```
   
   **Note:** Use double backslashes `\\` on Windows!

3. Save the file
4. **File → Sync Project with Gradle Files**

---

## Solution 3: Manually Add Run Configuration

If sync doesn't create the run configuration automatically:

### Step 1: Add Configuration
1. Click the dropdown next to the Run button (top right)
2. Click **Edit Configurations...**
3. Click the **+** button (top left)
4. Select **Android App**

### Step 2: Configure
- **Name**: `app`
- **Module**: Select `VyapaarSetu_AI_Tester.app.main` (or similar)
- **Installation option**: Default APK
- **Launch**: Default Activity
- Click **OK**

### Step 3: Run
- Click the green Run button (▶️)
- Select your device/emulator
- App should launch

---

## Solution 4: Check Project Structure

### Verify Files Exist
Make sure these files exist:

```
VyapaarSetuAITester/
├── build.gradle.kts ✅
├── settings.gradle.kts ✅
├── gradle.properties ✅
├── local.properties (create if missing)
└── app/
    ├── build.gradle.kts ✅
    └── src/
        └── main/
            ├── AndroidManifest.xml ✅
            └── java/com/vyapaarsetu/aitester/
                ├── MainActivity.kt ✅
                └── VyapaarSetuApp.kt ✅
```

### Missing Files?
If any files are missing, the project won't build. Check:
- `settings.gradle.kts` - Should include `:app` module
- `app/build.gradle.kts` - Should have `com.android.application` plugin
- `AndroidManifest.xml` - Should declare MainActivity

---

## Solution 5: Clean and Rebuild

### Step 1: Clean
1. **Build → Clean Project**
2. Wait for completion

### Step 2: Rebuild
1. **Build → Rebuild Project**
2. Wait for build to complete
3. Check "Build" tab for errors

### Step 3: Sync Again
1. **File → Sync Project with Gradle Files**
2. Run configuration should appear

---

## Solution 6: Check Gradle Wrapper

### Verify Gradle Files
Make sure these exist:
```
VyapaarSetuAITester/
├── gradle/
│   └── wrapper/
│       ├── gradle-wrapper.jar
│       └── gradle-wrapper.properties
└── gradlew.bat (Windows)
```

### If Missing
1. Close Android Studio
2. Delete `.gradle` folder in project root
3. Reopen project in Android Studio
4. Let it recreate Gradle wrapper

---

## Solution 7: Import Project Correctly

### Make Sure You Opened the Right Folder

**CORRECT** ✅:
```
Open: C:\Users\Admin\Desktop\mlpart\Athernex\VyapaarSetuAITester
```

**WRONG** ❌:
```
Open: C:\Users\Admin\Desktop\mlpart\Athernex
Open: C:\Users\Admin\Desktop\mlpart\Athernex\VyapaarSetuAITester\app
```

### Re-import if Needed
1. Close project
2. **File → Close Project**
3. **Open** → Navigate to `VyapaarSetuAITester` folder
4. Click **OK**

---

## Solution 8: Check Android Studio Version

### Minimum Requirements
- **Android Studio**: Hedgehog (2023.1.1) or later
- **JDK**: 17 or higher
- **Gradle**: 8.2 or higher (handled automatically)

### Update if Needed
1. **Help → Check for Updates**
2. Install any available updates
3. Restart Android Studio

---

## Solution 9: Invalidate Caches (Nuclear Option)

If nothing else works:

1. **File → Invalidate Caches...**
2. Check ALL boxes:
   - ✅ Clear file system cache and Local History
   - ✅ Clear downloaded shared indexes
   - ✅ Clear VCS Log caches and indexes
3. Click **Invalidate and Restart**
4. Wait for restart and re-indexing (can take 5-10 minutes)
5. **File → Sync Project with Gradle Files**

---

## Solution 10: Create Gradle Wrapper (If Missing)

If Gradle wrapper is missing:

### Windows Command Prompt:
```cmd
cd C:\Users\Admin\Desktop\mlpart\Athernex\VyapaarSetuAITester
gradle wrapper --gradle-version 8.2
```

Then reopen in Android Studio.

---

## Verification Checklist

After applying fixes, verify:

- [ ] Gradle sync completes successfully
- [ ] No errors in "Build" tab
- [ ] Run configuration appears in dropdown (top right)
- [ ] Green Run button (▶️) is enabled
- [ ] Project structure shows `app` module
- [ ] `local.properties` exists with correct SDK path

---

## Common Error Messages

### "SDK location not found"
**Fix:** Create `local.properties` with SDK path (Solution 2)

### "Plugin [id: 'com.android.application'] was not found"
**Fix:** Check internet connection, sync Gradle again

### "Minimum supported Gradle version is X.X"
**Fix:** Update Gradle wrapper version in `gradle/wrapper/gradle-wrapper.properties`

### "Could not resolve all dependencies"
**Fix:** Check internet connection, clear Gradle cache:
```
File → Settings → Build, Execution, Deployment → Build Tools → Gradle
Click "Clear Gradle Cache"
```

### "No module selected"
**Fix:** Manually add run configuration (Solution 3)

---

## Still Not Working?

### Check These:

1. **Internet Connection**: Gradle needs to download dependencies
2. **Antivirus/Firewall**: May block Gradle downloads
3. **Disk Space**: Need at least 5GB free
4. **Permissions**: Run Android Studio as Administrator (Windows)

### Get Detailed Logs:

1. **Help → Show Log in Explorer**
2. Open `idea.log`
3. Look for error messages
4. Search for "ERROR" or "EXCEPTION"

### Last Resort:

1. Close Android Studio
2. Delete these folders:
   - `VyapaarSetuAITester/.gradle`
   - `VyapaarSetuAITester/.idea`
   - `VyapaarSetuAITester/app/build`
3. Reopen project
4. Let Android Studio recreate everything

---

## Quick Command Reference

### Sync Gradle:
```
File → Sync Project with Gradle Files
```

### Invalidate Caches:
```
File → Invalidate Caches → Invalidate and Restart
```

### Clean Build:
```
Build → Clean Project
Build → Rebuild Project
```

### Add Configuration:
```
Run → Edit Configurations → + → Android App
```

---

## Success Indicators

You'll know it's working when:

✅ Gradle sync shows "BUILD SUCCESSFUL"
✅ Run configuration dropdown shows "app"
✅ Green Run button (▶️) is enabled
✅ Project structure shows modules correctly
✅ No red errors in "Build" tab

---

## Need More Help?

See also:
- [QUICK_OPEN_GUIDE.md](QUICK_OPEN_GUIDE.md) - Basic opening instructions
- [ANDROID_STUDIO_SETUP.md](ANDROID_STUDIO_SETUP.md) - Detailed setup guide
- [README.md](README.md) - Project overview

---

**Most Common Solution**: File → Sync Project with Gradle Files + Create local.properties with SDK path
