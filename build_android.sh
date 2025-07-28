#!/bin/bash
# Android APK Build Script for GitHub Codespaces

echo "🚀 MOBILE TRADING ASSISTANT - ANDROID BUILD"
echo "=========================================="

# Set up environment
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y git zip unzip openjdk-8-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip
pip install buildozer cython
pip install -r requirements.txt

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf .buildozer/
rm -rf bin/

# Build APK
echo "🔨 Building Android APK..."
buildozer android debug

# Check result
if [ -f bin/*.apk ]; then
    echo "✅ APK built successfully!"
    echo "📱 APK location: $(ls bin/*.apk)"
    echo "📂 Download from the Files panel"
else
    echo "❌ APK build failed"
    echo "📝 Check build logs above"
fi

echo "🎉 Build process complete!"
