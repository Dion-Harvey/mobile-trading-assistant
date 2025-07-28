#!/bin/bash
# Simple Android APK Build Script - Fixed Buildozer PATH Issue

echo "🚀 MOBILE TRADING ASSISTANT - ANDROID BUILD (SIMPLIFIED)"
echo "========================================================="

# Function to check command success
check_success() {
    if [ $? -ne 0 ]; then
        echo "❌ Error: $1 failed"
        exit 1
    fi
}

# Update system first
echo "📦 Updating system packages..."
sudo apt-get update -qq
sudo apt-get install -y python3-pip python3-dev build-essential git zip unzip openjdk-8-jdk
check_success "System packages installation"

# Set up Java environment
echo "☕ Setting up Java environment..."
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
java -version
check_success "Java setup"

# Install Python packages with --user flag
echo "🐍 Installing Python packages..."
python3 -m pip install --user --upgrade pip setuptools wheel
python3 -m pip install --user buildozer==1.5.0 cython==3.0.11 kivy==2.3.1 colorama plyer
check_success "Python packages installation"

# Add user bin directory to PATH
export PATH=$PATH:$HOME/.local/bin

# Verify buildozer is accessible
echo "🔧 Checking buildozer installation..."
if command -v buildozer >/dev/null 2>&1; then
    echo "✅ Buildozer found: $(which buildozer)"
    buildozer --version
else
    echo "⚠️ Buildozer not found in PATH, trying direct installation..."
    python3 -m pip install --force-reinstall --user buildozer==1.5.0
    export PATH=$PATH:$HOME/.local/bin:/usr/local/bin
    
    if command -v buildozer >/dev/null 2>&1; then
        echo "✅ Buildozer now found: $(which buildozer)"
        buildozer --version
    else
        echo "❌ Buildozer still not found. Trying system-wide install..."
        sudo python3 -m pip install buildozer==1.5.0
        check_success "System-wide buildozer installation"
    fi
fi

# Clean any previous builds
echo "🧹 Cleaning previous builds..."
rm -rf .buildozer/
rm -rf bin/
mkdir -p bin/

# Verify all our Python files are present
echo "📋 Verifying project files..."
required_files=("mobile_trading_ui.py" "position_manager.py" "mobile_trading_pairs.py" "main.py" "buildozer.spec")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    else
        echo "✅ Found: $file"
    fi
done

# Set Android environment variables
export ANDROID_HOME=$HOME/.buildozer/android/platform/android-sdk
export ANDROID_SDK_ROOT=$ANDROID_HOME
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

# Build the APK
echo "🔨 Building Android APK..."
echo "⏰ This will take 15-20 minutes for first build..."

buildozer android debug 2>&1 | tee build.log

# Check if APK was created
if ls bin/*.apk >/dev/null 2>&1; then
    echo ""
    echo "🎉 SUCCESS! APK built successfully!"
    echo "📱 APK file: $(ls -la bin/*.apk)"
    echo "📏 File size: $(du -h bin/*.apk | cut -f1)"
    echo ""
    echo "📋 NEXT STEPS:"
    echo "1. Download the APK from the Files panel"
    echo "2. Transfer to your Android device"
    echo "3. Enable 'Install from unknown sources' in Android settings"
    echo "4. Install the APK and enjoy your mobile trading app!"
    echo ""
    echo "🎯 YOUR MOBILE TRADING APP FEATURES:"
    echo "   ✅ 50+ Trading Pairs with AI Recommendations"
    echo "   ✅ Automated Position Management"
    echo "   ✅ Real-time Alerts and Portfolio Tracking"
else
    echo ""
    echo "❌ APK build failed"
    echo "📋 Check the build.log file for details"
    echo ""
    echo "🔍 TROUBLESHOOTING:"
    echo "1. Check the last few lines of build.log for specific errors"
    echo "2. Ensure all Python imports work correctly"
    echo "3. Verify buildozer.spec configuration"
    echo ""
    echo "📄 Last 30 lines of build log:"
    tail -30 build.log
fi

echo ""
echo "🏁 Build process completed!"
