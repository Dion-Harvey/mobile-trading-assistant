#!/bin/bash
# Android APK Build Script for GitHub Codespaces - Enhanced Error Handling

echo "🚀 MOBILE TRADING ASSISTANT - ANDROID BUILD"
echo "=========================================="

# Function to check command success
check_success() {
    if [ $? -ne 0 ]; then
        echo "❌ Error: $1 failed"
        exit 1
    fi
}

# Set up environment
echo "⚙️ Setting up environment..."
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
export ANDROID_HOME=$HOME/.buildozer/android/platform/android-sdk
export ANDROID_SDK_ROOT=$ANDROID_HOME
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

# Update system and install dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update -qq
check_success "System update"

sudo apt-get install -y \
    git zip unzip openjdk-8-jdk python3-pip python3-dev \
    autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev \
    build-essential libltdl-dev ccache
check_success "System dependencies installation"

# Verify Java installation
echo "☕ Verifying Java installation..."
java -version
check_success "Java verification"

# Install Python dependencies with specific versions
echo "🐍 Installing Python dependencies..."
python3 -m pip install --upgrade pip setuptools wheel
check_success "Pip upgrade"

python3 -m pip install --user \
    buildozer==1.5.0 \
    cython==3.0.11 \
    kivy==2.3.1 \
    colorama \
    plyer
check_success "Python dependencies installation"

# Add user bin to PATH for buildozer
export PATH=$PATH:$HOME/.local/bin

# Verify buildozer installation
echo "🔧 Verifying buildozer installation..."
which buildozer
if [ $? -ne 0 ]; then
    echo "⚠️ Buildozer not in PATH, trying alternative installation..."
    python3 -m pip install --force-reinstall buildozer==1.5.0
    export PATH=$PATH:/usr/local/bin:$HOME/.local/bin
fi

buildozer --version
check_success "Buildozer verification"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf .buildozer/
rm -rf bin/
mkdir -p bin/

# Initialize buildozer if needed
if [ ! -f buildozer.spec ]; then
    echo "📋 Initializing buildozer..."
    buildozer init
    check_success "Buildozer initialization"
fi

# Fix common buildozer.spec issues
echo "🔧 Fixing buildozer configuration..."
if grep -q "android.gradle_dependencies" buildozer.spec; then
    echo "✅ Gradle dependencies already configured"
else
    echo "android.gradle_dependencies = " >> buildozer.spec
fi

# Build APK with verbose output
echo "🔨 Building Android APK (this may take 10-20 minutes)..."
echo "📝 Building with verbose output for debugging..."

buildozer android debug --verbose 2>&1 | tee build.log

# Check build result
if [ -f bin/*.apk ]; then
    echo "✅ APK built successfully!"
    echo "📱 APK location: $(ls -la bin/*.apk)"
    echo "📂 File size: $(du -h bin/*.apk | cut -f1)"
    echo ""
    echo "🎯 NEXT STEPS:"
    echo "1. Download the APK from the Files panel"
    echo "2. Transfer to your Android device"
    echo "3. Enable 'Install from unknown sources'"
    echo "4. Install and enjoy your mobile trading app!"
else
    echo "❌ APK build failed"
    echo "� Build log saved to build.log"
    echo "🔍 Last 20 lines of build log:"
    tail -20 build.log
    echo ""
    echo "🛠️ TROUBLESHOOTING:"
    echo "1. Check if all dependencies are in requirements.txt"
    echo "2. Verify Python import statements"
    echo "3. Check buildozer.spec configuration"
    echo "4. Review full build.log for specific errors"
fi

echo "🎉 Build process complete!"
