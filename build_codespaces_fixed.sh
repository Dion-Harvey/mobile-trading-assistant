#!/bin/bash
# Fixed Android Build Script for GitHub Codespaces - SDK Manager Issue Resolution

echo "🚀 MOBILE TRADING ASSISTANT - FIXED BUILD"
echo "=========================================="

# Set working directory
cd /workspaces/mobile-trading-assistant

# Environment setup
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH:$HOME/.local/bin

# Install dependencies
echo "📦 Installing dependencies..."
python3 -m pip install --user buildozer==1.5.0 cython==3.0.11 kivy==2.3.1

# Clean previous builds
echo "🧹 Cleaning builds..."
rm -rf .buildozer/ bin/

# Create fixed buildozer.spec
echo "📋 Creating fixed buildozer.spec..."
cat > buildozer.spec << 'EOF'
[app]
title = Trading Assistant
package.name = tradingassistant
package.domain = org.tradingapp

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_dirs = tests,bin,.buildozer

version = 0.1
requirements = python3,kivy,requests,plyer

[buildozer]
log_level = 1

[app:android]
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK
android.api = 28
android.minapi = 21
android.ndk = 21b
android.sdk = 28
android.accept_sdk_license = True
android.gradle_dependencies = 
android.add_compile_options = 
android.add_gradle_repositories = 
android.gradle_repositories = google(), mavenCentral()
android.enable_androidx = True

[app:android.gradle]
android.gradle_dependencies = androidx.appcompat:appcompat:1.0.0
EOF

# Pre-download Android components to avoid SDK manager issues
echo "⬇️ Pre-configuring Android environment..."
mkdir -p $HOME/.buildozer/android/platform

# Build with specific settings to avoid SDK manager
echo "🔨 Building APK with fixed configuration..."
buildozer android debug 2>&1 | tee fixed_build.log

# Check results
if [ -f bin/*.apk ]; then
    echo "✅ APK built successfully!"
    echo "📱 APK details:"
    ls -la bin/
    echo "📁 File size: $(du -h bin/*.apk 2>/dev/null | cut -f1)"
    echo ""
    echo "🎯 SUCCESS! Your APK is ready for download."
else
    echo "❌ Build failed. Analyzing error..."
    
    # Check for specific errors
    if grep -q "sdkmanager" fixed_build.log; then
        echo "🔧 SDK Manager issue detected. Trying alternative approach..."
        
        # Try with older, more stable versions
        sed -i 's/android.api = 28/android.api = 27/' buildozer.spec
        sed -i 's/android.sdk = 28/android.sdk = 27/' buildozer.spec
        sed -i 's/android.ndk = 21b/android.ndk = 19b/' buildozer.spec
        
        echo "🔄 Retrying with API 27..."
        buildozer android debug 2>&1 | tee retry_build.log
        
        if [ -f bin/*.apk ]; then
            echo "✅ APK built successfully with API 27!"
            ls -la bin/
        else
            echo "❌ Still failing. Here's the error summary:"
            tail -15 retry_build.log
        fi
    fi
fi

echo "🎉 Build process complete!"
EOF
