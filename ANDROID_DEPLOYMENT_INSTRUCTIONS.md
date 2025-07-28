# ANDROID DEPLOYMENT - STEP BY STEP GUIDE FOR WINDOWS
# Complete instructions to get your trading app on Android

## OPTION 1: RECOMMENDED - Using WSL (Windows Subsystem for Linux)

### Step 1: Install WSL
# Open PowerShell as Administrator and run:
wsl --install

# Reboot your computer
# Open Ubuntu from Start Menu

### Step 2: Install Dependencies in WSL
# Update system
sudo apt update
sudo apt install -y git zip unzip openjdk-8-jdk python3-pip

# Install Python dependencies
pip3 install kivy[base]
pip3 install buildozer
pip3 install cython

# Install build dependencies
sudo apt install -y build-essential libssl-dev libffi-dev
sudo apt install -y libsqlite3-dev sqlite3 bzip2 libbz2-dev

### Step 3: Copy Your Project to WSL
# In WSL terminal, navigate to your home directory
cd ~

# Create project directory
mkdir crypto-trading-app
cd crypto-trading-app

# Copy files from Windows (adjust path as needed)
cp /mnt/c/Users/miste/Documents/"Trading Assistant Market Analyzer"/*.py .
cp /mnt/c/Users/miste/Documents/"Trading Assistant Market Analyzer"/buildozer.spec .

### Step 4: Build APK
# First build (takes 30-60 minutes)
buildozer android debug

# Your APK will be in: bin/cryptotradingassistant-1.0-armeabi-v7a-debug.apk

## OPTION 2: Direct Windows Installation (More Complex)

### Step 1: Install Dependencies
pip install kivy[base]
pip install buildozer
pip install cython

### Step 2: Install Java JDK 8
# Download from: https://adoptium.net/temurin/releases/
# Set JAVA_HOME environment variable

### Step 3: Build APK
buildozer android debug

## INSTALLING ON YOUR ANDROID PHONE

### Method 1: USB Installation
1. Enable Developer Options:
   - Go to Settings → About Phone
   - Tap "Build Number" 7 times
   - Go back to Settings → Developer Options
   - Enable "USB Debugging"

2. Connect phone to computer
3. Install ADB (Android Debug Bridge)
4. Run: adb install bin/cryptotradingassistant-1.0-armeabi-v7a-debug.apk

### Method 2: Direct Installation
1. Copy APK file to your phone
2. Enable "Install from Unknown Sources" in Settings
3. Tap the APK file to install

## TROUBLESHOOTING

### Build Fails
- Run: buildozer android clean
- Try again: buildozer android debug

### Java Not Found
- Install OpenJDK 8
- Set JAVA_HOME environment variable

### Permission Errors (Linux/WSL)
sudo chown -R $USER ~/.buildozer

### App Crashes on Phone
- Check logs: adb logcat | grep python
- Add missing dependencies to buildozer.spec requirements

## TESTING YOUR APP

Once installed, your app will have:
✅ 50+ trading pairs monitoring
✅ Buy/sell recommendations
✅ Position management
✅ Real-time alerts
✅ Portfolio tracking

The app will work offline for basic functions and online for real-time data.

## PERFORMANCE TIPS

- First launch may be slow (initializing)
- Grant internet permission when prompted
- Allow notifications for alerts
- Keep app updated through manual APK installation

Your crypto trading assistant is now ready for mobile use!
