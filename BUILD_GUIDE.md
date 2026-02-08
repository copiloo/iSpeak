# iSpeak Swift - Build & Distribution Guide

Step-by-step guide for building, signing, and distributing iSpeak.

---

## Prerequisites

### Development Environment
- **Xcode:** 15.0 or later
- **macOS:** 14.0 (Sonoma) or later for development
- **Apple Developer Account:** Required for code signing and notarization
- **Command Line Tools:** `xcode-select --install`

### Certificates & Provisioning
1. **Developer ID Application Certificate:**
   - Log in to [Apple Developer Portal](https://developer.apple.com)
   - Navigate to Certificates, Identifiers & Profiles
   - Create new "Developer ID Application" certificate
   - Download and install in Keychain

2. **App ID:**
   - Create App ID: `com.yourname.iSpeak`
   - Enable App Sandbox capability

---

## Building for Development

### 1. Open Project in Xcode

```bash
cd /path/to/iSpeak-Swift/iSpeak
open iSpeak.xcodeproj
```

### 2. Configure Signing

1. Select **iSpeak** target
2. Go to **Signing & Capabilities** tab
3. **Automatically manage signing:** Enabled
4. **Team:** Select your Apple Developer team
5. **Bundle Identifier:** Update to your unique ID (e.g., `com.yourname.iSpeak`)

### 3. Verify Entitlements

Check `iSpeak.entitlements` contains:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- Sandbox -->
    <key>com.apple.security.app-sandbox</key>
    <true/>

    <!-- Microphone access -->
    <key>com.apple.security.device.audio-input</key>
    <true/>

    <!-- Input monitoring (hotkey) -->
    <key>com.apple.security.personal-information.input-monitoring</key>
    <true/>

    <!-- Apple Events (text injection) -->
    <key>com.apple.security.automation.apple-events</key>
    <true/>

    <!-- Network (for model downloads) -->
    <key>com.apple.security.network.client</key>
    <true/>

    <!-- User Selected Files (vocabulary.json) -->
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
</dict>
</plist>
```

### 4. Build & Run

```bash
# Debug build (Cmd+R in Xcode)
# Or via command line:
xcodebuild -project iSpeak.xcodeproj \
           -scheme iSpeak \
           -configuration Debug \
           build
```

---

## Building for Release

### 1. Update Version Number

In `iSpeak.xcodeproj` → **General** tab:
- **Version:** 1.0.0 (CFBundleShortVersionString)
- **Build:** 1 (CFBundleVersion)

### 2. Configure Release Build Settings

1. Select **iSpeak** target
2. **Build Settings** tab
3. Set **Configuration** to **Release**
4. Verify these settings:
   - **Optimization Level:** `-O` (Optimize for Speed)
   - **Swift Optimization Level:** `-Osize` (Optimize for Size)
   - **Strip Debug Symbols:** Yes
   - **Strip Swift Symbols:** Yes

### 3. Archive the App

```bash
# Via Xcode: Product → Archive
# Or command line:
xcodebuild -project iSpeak.xcodeproj \
           -scheme iSpeak \
           -configuration Release \
           -archivePath ./build/iSpeak.xcarchive \
           archive
```

### 4. Export App

```bash
# Via Xcode: Window → Organizer → Distribute App
# Or command line:
xcodebuild -exportArchive \
           -archivePath ./build/iSpeak.xcarchive \
           -exportPath ./build/export \
           -exportOptionsPlist ExportOptions.plist
```

**ExportOptions.plist:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>developer-id</string>
    <key>teamID</key>
    <string>YOUR_TEAM_ID</string>
    <key>signingCertificate</key>
    <string>Developer ID Application</string>
    <key>signingStyle</key>
    <string>manual</string>
</dict>
</plist>
```

---

## Code Signing

### Verify Signing

```bash
codesign -dv --verbose=4 ./build/export/iSpeak.app

# Should show:
# - Authority=Developer ID Application: Your Name (TEAM_ID)
# - Sealed Resources version=2
# - Identifier=com.yourname.iSpeak
```

### Manual Signing (if needed)

```bash
codesign --deep --force \
         --options runtime \
         --sign "Developer ID Application: Your Name (TEAM_ID)" \
         ./build/export/iSpeak.app

# Verify
codesign -v --verbose=4 ./build/export/iSpeak.app
```

---

## Notarization

### 1. Create App-Specific Password

1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Sign in with Apple ID
3. **App-Specific Passwords** → Generate new
4. Save password securely

### 2. Store Credentials in Keychain

```bash
xcrun notarytool store-credentials "notarytool-profile" \
         --apple-id "your@email.com" \
         --team-id "YOUR_TEAM_ID" \
         --password "xxxx-xxxx-xxxx-xxxx"
```

### 3. Create ZIP for Notarization

```bash
cd ./build/export
ditto -c -k --keepParent iSpeak.app iSpeak.zip
```

### 4. Submit for Notarization

```bash
xcrun notarytool submit iSpeak.zip \
         --keychain-profile "notarytool-profile" \
         --wait

# Wait for response (5-30 minutes typically)
```

### 5. Check Notarization Status

```bash
# If submission UUID is abc-123-def
xcrun notarytool info abc-123-def \
         --keychain-profile "notarytool-profile"

# Check log for issues
xcrun notarytool log abc-123-def \
         --keychain-profile "notarytool-profile" \
         notarization-log.json
```

### 6. Staple Notarization Ticket

```bash
xcrun stapler staple ./build/export/iSpeak.app

# Verify
xcrun stapler validate ./build/export/iSpeak.app
spctl -a -v ./build/export/iSpeak.app
```

---

## Creating DMG Installer

### 1. Prepare DMG Directory

```bash
mkdir -p ./dmg-temp
cp -R ./build/export/iSpeak.app ./dmg-temp/
ln -s /Applications ./dmg-temp/Applications
```

### 2. Create DMG

```bash
hdiutil create -volname "iSpeak" \
         -srcfolder ./dmg-temp \
         -ov -format UDZO \
         ./build/iSpeak.dmg
```

### 3. Notarize DMG (Optional but Recommended)

```bash
xcrun notarytool submit ./build/iSpeak.dmg \
         --keychain-profile "notarytool-profile" \
         --wait

xcrun stapler staple ./build/iSpeak.dmg
```

### 4. Verify DMG

```bash
# Mount and test
hdiutil attach ./build/iSpeak.dmg
# Drag iSpeak.app to Applications
# Launch and verify
```

---

## Distribution Checklist

### Pre-Release
- [ ] Version number updated
- [ ] CHANGELOG.md created
- [ ] All tests passing (see TESTING.md)
- [ ] Documentation complete
- [ ] Known issues documented

### Build Process
- [ ] Archive created successfully
- [ ] App exported with Developer ID
- [ ] Code signature verified
- [ ] Hardened runtime enabled
- [ ] Entitlements correct

### Notarization
- [ ] App notarized by Apple
- [ ] Notarization ticket stapled
- [ ] Gatekeeper validation passes
- [ ] Fresh Mac test successful

### Installer
- [ ] DMG created
- [ ] DMG notarized (optional)
- [ ] DMG opens correctly
- [ ] App installs to /Applications
- [ ] App launches after install

### Release
- [ ] GitHub release created
- [ ] Release notes published
- [ ] DMG uploaded
- [ ] Checksums provided (SHA256)

---

## Troubleshooting

### Common Build Issues

**Issue:** "No signing certificate found"
```bash
# Solution: Install Developer ID certificate from Apple Developer portal
# Verify in Keychain Access
```

**Issue:** "Entitlements not valid"
```bash
# Solution: Check iSpeak.entitlements matches required permissions
# Verify App ID capabilities in Developer portal
```

**Issue:** "Architecture mismatch"
```bash
# Solution: Set ARCHS to "arm64" for Apple Silicon or "x86_64 arm64" for Universal
# Build Settings → Architectures
```

### Notarization Issues

**Issue:** "Invalid binary"
```bash
# Check notarization log:
xcrun notarytool log SUBMISSION_ID \
      --keychain-profile "notarytool-profile" \
      log.json
cat log.json | jq '.issues'
```

**Issue:** "Hardened runtime not enabled"
```bash
# Add --options runtime to codesign:
codesign --options runtime --sign "Developer ID" iSpeak.app
```

**Issue:** "Invalid entitlements"
```bash
# Some entitlements require App Sandbox
# Verify all entitlements are sandbox-compatible
```

### Gatekeeper Issues

**Issue:** "App damaged" or "Cannot open"
```bash
# Remove quarantine attribute:
xattr -cr /Applications/iSpeak.app

# Verify Gatekeeper allows:
spctl -a -v /Applications/iSpeak.app
```

---

## Continuous Integration (Optional)

### GitHub Actions Example

```yaml
name: Build and Notarize

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: macos-14
    steps:
      - uses: actions/checkout@v3

      - name: Setup Xcode
        uses: maxim-lobanov/setup-xcode@v1
        with:
          xcode-version: '15.0'

      - name: Build
        run: |
          xcodebuild -project iSpeak.xcodeproj \
                     -scheme iSpeak \
                     -configuration Release \
                     -archivePath ./iSpeak.xcarchive \
                     archive

      - name: Export
        run: |
          xcodebuild -exportArchive \
                     -archivePath ./iSpeak.xcarchive \
                     -exportPath ./export \
                     -exportOptionsPlist ExportOptions.plist

      - name: Notarize
        env:
          APPLE_ID: ${{ secrets.APPLE_ID }}
          TEAM_ID: ${{ secrets.TEAM_ID }}
          APP_PASSWORD: ${{ secrets.APP_PASSWORD }}
        run: |
          # Store credentials
          xcrun notarytool store-credentials "ci-profile" \
                --apple-id "$APPLE_ID" \
                --team-id "$TEAM_ID" \
                --password "$APP_PASSWORD"

          # Create ZIP
          ditto -c -k --keepParent ./export/iSpeak.app iSpeak.zip

          # Submit
          xcrun notarytool submit iSpeak.zip \
                --keychain-profile "ci-profile" \
                --wait

          # Staple
          xcrun stapler staple ./export/iSpeak.app

      - name: Create DMG
        run: |
          mkdir dmg-temp
          cp -R ./export/iSpeak.app ./dmg-temp/
          ln -s /Applications ./dmg-temp/Applications
          hdiutil create -volname "iSpeak" \
                  -srcfolder ./dmg-temp \
                  -ov -format UDZO \
                  iSpeak.dmg

      - name: Upload Release
        uses: actions/upload-artifact@v3
        with:
          name: iSpeak-DMG
          path: iSpeak.dmg
```

---

## Release Workflow

### 1. Prepare Release

```bash
# Update version
# Update CHANGELOG.md
# Run all tests
# Commit changes
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### 2. Build & Sign

```bash
./scripts/build-release.sh  # If you create automation script
```

### 3. Test on Clean Mac

- Download DMG
- Mount and install
- Launch app
- Verify all functionality

### 4. Publish

```bash
# Create GitHub release
gh release create v1.0.0 \
   --title "iSpeak v1.0.0" \
   --notes "Release notes here" \
   ./build/iSpeak.dmg
```

---

## Security Considerations

### Code Signing Best Practices
- Never commit certificates to version control
- Store credentials in Keychain or CI secrets
- Use app-specific passwords for notarization
- Rotate passwords periodically

### Sandboxing
- App Sandbox is ENABLED by default
- All file access requires user selection or entitlements
- Network access limited to necessary services
- Input monitoring permission required for hotkey

### Privacy
- All transcription happens offline (no data sent to servers)
- User's voice data never leaves their Mac
- Privacy policy: state clearly that no data is collected

---

## Maintenance

### Updating Dependencies
- WhisperKit: Check for updates periodically
- Update min macOS version if needed
- Test thoroughly after dependency updates

### Versioning
- **Major (X.0.0):** Breaking changes, major features
- **Minor (1.X.0):** New features, enhancements
- **Patch (1.0.X):** Bug fixes, minor improvements

---

**Ready to distribute!** 🚀

For support during build process:
- Check Xcode logs
- Review Apple Developer documentation
- Test on multiple machines before public release
