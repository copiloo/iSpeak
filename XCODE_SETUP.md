# Xcode Project Configuration Guide

This guide covers the remaining manual Xcode configuration steps to complete Phase 1 setup.

## ✅ Already Completed

- ✅ Created Xcode project structure
- ✅ Created entitlements file (`iSpeak.entitlements`)
- ✅ Created Info.plist with permission keys
- ✅ Created AppDelegate and MenuBarController
- ✅ Updated iSpeakApp.swift for menu bar app
- ✅ Copied icon and vocabulary resources

## 📋 Remaining Steps (Must do in Xcode)

### 1. Add Files to Xcode Project

**Important:** The files we created are on disk but not yet added to the Xcode project.

1. Open Xcode and load the project: `/Users/kid/Documents/MyProjects/Development projects/MERNProjects/iSpeak-Swift/iSpeak/iSpeak.xcodeproj`

2. In Project Navigator (left sidebar), **delete** the old `iSpeakApp.swift` reference if it exists at the root level (it will show in red as missing)

3. **Right-click on the `iSpeak` folder** → Select "Add Files to iSpeak..."

4. Navigate to and add these **folders** (make sure "Create folder references" is selected):
   - `App` folder
   - `UI` folder
   - `Services` folder (currently empty, but needed for structure)
   - `Hotkeys` folder (currently empty)
   - `Models` folder (currently empty)
   - `Resources` folder

5. After adding, your project navigator should show:
   ```
   iSpeak/
   ├── App/
   │   ├── iSpeakApp.swift
   │   └── AppDelegate.swift
   ├── UI/
   │   └── MenuBar/
   │       └── MenuBarController.swift
   ├── Services/
   ├── Hotkeys/
   ├── Models/
   ├── Resources/
   │   ├── icon.icns
   │   └── Dictionaries/
   │       └── vocabulary.json
   └── Assets.xcassets/
   ```

6. You can **delete** `ContentView.swift` - we don't need it (menu bar only app)

---

### 2. Configure Build Settings

1. Click on **iSpeak project** (blue icon) in Project Navigator
2. Select **iSpeak target** (under TARGETS)
3. Go to **Signing & Capabilities** tab

#### Add Capabilities:
Click **+ Capability** button and add:
- App Sandbox ✓
- Hardened Runtime ✓

Under **App Sandbox**, enable:
- ✓ Incoming Connections (Audio Input)
- ✓ Outgoing Connections (Network for model downloads)
- ✓ Hardware → Audio Input

Under **Hardened Runtime**, enable:
- ✓ Audio Input

---

### 3. Link Entitlements File

Still in **Signing & Capabilities** tab:

1. Scroll to find **App Sandbox** section
2. Look for "Entitlements File" field
3. Click the folder icon and select `iSpeak/iSpeak.entitlements`

OR:

1. Go to **Build Settings** tab
2. Search for "Code Signing Entitlements"
3. Set value to: `iSpeak/iSpeak.entitlements`

---

### 4. Link Info.plist

1. Still in **Build Settings** tab
2. Search for "Info.plist File"
3. Set value to: `iSpeak/Info.plist`

OR verify in **Info** tab that Info.plist is correctly linked.

---

### 5. Add WhisperKit Package Dependency

This is the ML transcription library we'll use in Phase 3.

1. With the project selected, go to **File → Add Package Dependencies...**

2. In the search field, paste:
   ```
   https://github.com/argmaxinc/WhisperKit
   ```

3. Click **Add Package**

4. In the "Choose Package Products" dialog:
   - Select **WhisperKit** (checked)
   - Add to target: **iSpeak**

5. Click **Add Package**

Note: This may take a minute to fetch and build the package. You'll see build activity in the top toolbar.

---

### 6. Set App Icon

1. Open `Assets.xcassets` in Project Navigator
2. Click on **AppIcon**
3. We'll use the menu bar icon programmatically (already done in MenuBarController.swift)
4. For the app icon (shown in Finder, dock if shown), you can:
   - Drag `Resources/icon.icns` into each size slot, OR
   - Leave empty for now (not critical for menu bar app)

---

### 7. Set Minimum macOS Version

1. Project Settings → **General** tab
2. Find **Minimum Deployments**
3. Set to: **macOS 14.0** (required for Observation framework)

---

### 8. Configure Scheme (Optional but Recommended)

This ensures you're building for the correct architecture.

1. Click the scheme dropdown (near Play/Stop buttons) → **Edit Scheme...**
2. Select **Run** on the left
3. Go to **Info** tab
4. Set **Build Configuration** to: **Debug**
5. Go to **Options** tab
6. Set **Architecture** to: **ARM64** (if on Apple Silicon Mac)

---

### 9. Build and Test

1. Click **Product → Build** (⌘B)

2. If build succeeds:
   - Click **Product → Run** (⌘R)
   - You should see a microphone icon appear in the menu bar
   - Click it to see the menu with Language, Model, Settings, and Quit options

3. **Expected behavior:**
   - No window appears (menu bar only)
   - Icon appears in system menu bar
   - Clicking icon shows menu
   - Language and Model selections show checkmarks
   - Clicking selections prints to console (Xcode debug area)

4. **If build fails:**
   - Check Console (View → Debug Area → Show Debug Area)
   - Common issues:
     - Missing file references (fix: verify files are added to project)
     - Entitlements file not found (fix: verify path in Build Settings)
     - WhisperKit not found (fix: re-add package dependency)

---

### 10. Verify Structure

After building, verify the structure in Project Navigator matches:

```
iSpeak (blue icon - project)
└── iSpeak (folder)
    ├── App/
    │   ├── iSpeakApp.swift
    │   └── AppDelegate.swift
    ├── UI/
    │   └── MenuBar/
    │       └── MenuBarController.swift
    ├── Services/
    ├── Hotkeys/
    ├── Models/
    ├── Resources/
    │   ├── icon.icns
    │   └── Dictionaries/
    ├── Assets.xcassets/
    ├── iSpeak.entitlements
    └── Info.plist
└── iSpeakTests/
└── iSpeakUITests/
```

---

## 🎉 Phase 1 Complete!

Once the app builds and runs successfully:

**You've completed Phase 1 - Project Setup & Foundation!**

The menu bar app structure is in place. Next phases will add:
- Phase 2: Audio capture (AVFoundation)
- Phase 3: Transcription (WhisperKit)
- Phase 4: Hotkey system (CGEventTap)
- ...and more

---

## 🐛 Troubleshooting

### "Cannot find 'MenuBarController' in scope"
- Verify `MenuBarController.swift` is added to the project
- Check it's part of the iSpeak target (File Inspector → Target Membership)

### "Sandbox: deny(1) file-read-data"
- Check App Sandbox entitlements are correctly configured
- Verify entitlements file is linked in Build Settings

### WhisperKit won't download
- Check internet connection
- Try: Product → Clean Build Folder (⇧⌘K) then rebuild

### App crashes on launch
- Check Console for errors
- Verify Info.plist is linked correctly
- Check LSUIElement is set to true (menu bar only)

---

## 📝 Next Steps

After successful build and run:

1. Test the menu bar:
   - Click icon
   - Try selecting different languages (should see checkmark move)
   - Try selecting different models (should see checkmark move)
   - Toggle "Auto-press Enter" (should see checkmark)

2. Check debug console for print statements:
   - "Language changed to: ..."
   - "Model changed to: ..."
   - "Auto-enter: true/false"

3. Ready for Phase 2: Audio Capture!

---

*Created: 2026-02-06*
*Phase: 1 - Project Setup & Foundation*
