# Android Deployment Guide for Mobile Trading App
"""
COMPLETE GUIDE TO DEPLOY YOUR MOBILE TRADING APP ON ANDROID

This guide covers everything needed to get your trading app running on Android:
1. Setting up the development environment
2. Installing Buildozer (Kivy's Android packaging tool)
3. Configuring the build settings
4. Building the APK
5. Installing on your phone
6. Troubleshooting common issues
"""

import os
import subprocess
import platform

class AndroidDeploymentGuide:
    """Complete guide for Android deployment"""
    
    def __init__(self):
        self.os_type = platform.system()
        self.steps_completed = []
    
    def show_deployment_overview(self):
        """Show complete deployment overview"""
        print("📱 ANDROID DEPLOYMENT GUIDE")
        print("=" * 50)
        print("🎯 DEPLOYMENT STEPS:")
        print("1. ✅ Install Python dependencies")
        print("2. ✅ Install Buildozer (Android packaging tool)")
        print("3. ✅ Setup Android SDK/NDK (automated)")
        print("4. ✅ Configure buildozer.spec file")
        print("5. ✅ Build APK file")
        print("6. ✅ Install on Android phone")
        print("=" * 50)
        
    def check_prerequisites(self):
        """Check system prerequisites"""
        print("\n🔍 CHECKING PREREQUISITES...")
        print("-" * 30)
        
        # Check Python version
        python_version = platform.python_version()
        print(f"✅ Python version: {python_version}")
        
        # Check if Kivy is installed
        try:
            import kivy
            print(f"✅ Kivy installed: {kivy.__version__}")
        except ImportError:
            print("❌ Kivy not installed - will install automatically")
        
        # Check operating system
        if self.os_type == "Windows":
            print("💻 Windows detected - using WSL/Linux environment recommended")
        elif self.os_type == "Linux":
            print("✅ Linux detected - optimal for Android development")
        elif self.os_type == "Darwin":
            print("🍎 macOS detected - supported with some limitations")
        
        return True
    
    def generate_installation_commands(self):
        """Generate installation commands for different platforms"""
        print("\n📦 INSTALLATION COMMANDS")
        print("=" * 40)
        
        if self.os_type == "Windows":
            print("🪟 WINDOWS INSTALLATION:")
            print("# Option 1: Using Windows Subsystem for Linux (RECOMMENDED)")
            print("wsl --install")
            print("# Then follow Linux instructions inside WSL")
            print()
            print("# Option 2: Direct Windows installation")
            print("pip install kivy[base]")
            print("pip install buildozer")
            print("pip install cython")
            print()
            
        elif self.os_type == "Linux":
            print("🐧 LINUX INSTALLATION:")
            print("# Update system")
            print("sudo apt update")
            print("sudo apt install -y git zip unzip openjdk-8-jdk python3-pip")
            print()
            print("# Install Python dependencies")
            print("pip3 install kivy[base]")
            print("pip3 install buildozer")
            print("pip3 install cython")
            print()
            print("# Install additional build dependencies")
            print("sudo apt install -y build-essential libssl-dev libffi-dev")
            print("sudo apt install -y libsqlite3-dev sqlite3 bzip2 libbz2-dev")
            print()
            
        elif self.os_type == "Darwin":
            print("🍎 MACOS INSTALLATION:")
            print("# Install Homebrew if not installed")
            print('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
            print()
            print("# Install dependencies")
            print("brew install python3 java")
            print("pip3 install kivy[base]")
            print("pip3 install buildozer")
            print("pip3 install cython")
            print()
    
    def create_buildozer_spec(self):
        """Create buildozer.spec configuration file"""
        buildozer_config = """[app]

# Basic app information
title = Crypto Trading Assistant
package.name = cryptotradingassistant
package.domain = com.yourname.cryptotrading

# Source code
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json

# Version info
version = 1.0
version.regex = __version__ = ['"](.+)['"]
version.filename = %(source.dir)s/main.py

# Application requirements
requirements = python3,kivy,kivymd,requests,numpy,pandas,websocket-client,certifi

# Android specific
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK,VIBRATE
android.api = 31
android.minapi = 21
android.ndk = 23b
android.sdk = 31
android.accept_sdk_license = True

# App icon and presplash
#icon.filename = %(source.dir)s/data/icon.png
#presplash.filename = %(source.dir)s/data/presplash.png

# Orientation
orientation = portrait

# Services
#android.add_src = %(source.dir)s/src/android
#android.gradle_dependencies = 

# Build configuration
[buildozer]
log_level = 2
warn_on_root = 1

# Advanced
[app:android.gradle]
android.gradle_dependencies = androidx.work:work-runtime:2.7.1

[app:android.manifest]
android.uses_library = org.apache.http.legacy,required=false
"""
        
        with open("buildozer.spec", "w") as f:
            f.write(buildozer_config)
        
        print("✅ Created buildozer.spec configuration file")
        return "buildozer.spec"
    
    def create_main_app_file(self):
        """Create simplified main.py for deployment"""
        main_content = """#!/usr/bin/env python3
# Main entry point for Android deployment

__version__ = "1.0"

# Import error handling for missing modules
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import our mobile trading app
    from mobile_trading_ui import MobileTradingApp
    
    # Run the app
    if __name__ == '__main__':
        print("🚀 Starting Crypto Trading Assistant...")
        MobileTradingApp().run()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Creating basic Kivy app for testing...")
    
    # Fallback basic app
    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.boxlayout import BoxLayout
    
    class FallbackApp(App):
        def build(self):
            layout = BoxLayout(orientation='vertical')
            layout.add_widget(Label(text='Crypto Trading Assistant', font_size='20sp'))
            layout.add_widget(Label(text='Loading...', font_size='16sp'))
            return layout
    
    FallbackApp().run()
"""
        
        with open("main.py", "w") as f:
            f.write(main_content)
        
        print("✅ Created main.py entry point")
        return "main.py"
    
    def create_requirements_file(self):
        """Create requirements.txt for dependencies"""
        requirements = """# Core dependencies
kivy>=2.1.0
kivymd>=1.1.1

# Trading and data analysis
requests>=2.28.0
numpy>=1.21.0
pandas>=1.5.0
websocket-client>=1.4.0

# Crypto and networking
certifi>=2022.9.0
urllib3>=1.26.0

# Async support
asyncio-mqtt>=0.11.0

# Optional performance improvements
cython>=0.29.0
"""
        
        with open("requirements.txt", "w") as f:
            f.write(requirements)
        
        print("✅ Created requirements.txt")
        return "requirements.txt"
    
    def show_build_commands(self):
        """Show step-by-step build commands"""
        print("\n🔨 BUILD COMMANDS")
        print("=" * 30)
        print("1. Initialize buildozer (first time only):")
        print("   buildozer android debug")
        print()
        print("2. Clean build (if needed):")
        print("   buildozer android clean")
        print()
        print("3. Build APK:")
        print("   buildozer android debug")
        print()
        print("4. Build release APK (for distribution):")
        print("   buildozer android release")
        print()
        print("⏱️  First build takes 30-60 minutes (downloads Android SDK/NDK)")
        print("⏱️  Subsequent builds take 5-15 minutes")
    
    def show_installation_guide(self):
        """Show how to install APK on phone"""
        print("\n📱 INSTALL ON ANDROID PHONE")
        print("=" * 35)
        print("Method 1: USB Connection")
        print("1. Enable Developer Options on phone:")
        print("   Settings → About Phone → Tap 'Build Number' 7 times")
        print()
        print("2. Enable USB Debugging:")
        print("   Settings → Developer Options → USB Debugging")
        print()
        print("3. Connect phone to computer via USB")
        print()
        print("4. Install APK:")
        print("   adb install bin/cryptotradingassistant-1.0-armeabi-v7a-debug.apk")
        print()
        print("Method 2: Direct Transfer")
        print("1. Copy APK file to phone")
        print("2. Enable 'Install from Unknown Sources'")
        print("3. Tap APK file to install")
        print()
        print("Method 3: Google Play Console (for distribution)")
        print("1. Create Google Play Developer account ($25)")
        print("2. Upload signed APK")
        print("3. Publish to Play Store")
    
    def show_troubleshooting(self):
        """Show common issues and solutions"""
        print("\n🔧 TROUBLESHOOTING")
        print("=" * 25)
        print("Common Issues & Solutions:")
        print()
        print("❌ 'buildozer command not found'")
        print("✅ Solution: pip install --user buildozer")
        print("   Add ~/.local/bin to PATH")
        print()
        print("❌ 'Java not found'")
        print("✅ Solution: Install OpenJDK 8")
        print("   sudo apt install openjdk-8-jdk (Linux)")
        print("   brew install java (macOS)")
        print()
        print("❌ 'NDK/SDK download fails'")
        print("✅ Solution: Manual download")
        print("   buildozer android clean")
        print("   buildozer android debug")
        print()
        print("❌ 'Permission denied' on Linux")
        print("✅ Solution: Fix permissions")
        print("   sudo chown -R $USER ~/.buildozer")
        print()
        print("❌ 'App crashes on phone'")
        print("✅ Solution: Check logs")
        print("   adb logcat | grep python")
        print()
        print("❌ 'Import errors'")
        print("✅ Solution: Add to requirements in buildozer.spec")
        print("   requirements = python3,kivy,your_module")
    
    def show_optimization_tips(self):
        """Show app optimization tips"""
        print("\n⚡ OPTIMIZATION TIPS")
        print("=" * 25)
        print("🔋 Battery Optimization:")
        print("   • Reduce update frequency")
        print("   • Use background services sparingly")
        print("   • Implement app sleep mode")
        print()
        print("📱 Performance:")
        print("   • Limit concurrent connections")
        print("   • Use efficient data structures")
        print("   • Implement lazy loading")
        print()
        print("📊 Data Usage:")
        print("   • Cache market data")
        print("   • Compress API responses")
        print("   • Batch API calls")
        print()
        print("🎨 UI Optimization:")
        print("   • Use RecycleView for large lists")
        print("   • Optimize image sizes")
        print("   • Minimize layout complexity")
    
    def run_complete_guide(self):
        """Run the complete deployment guide"""
        self.show_deployment_overview()
        self.check_prerequisites()
        self.generate_installation_commands()
        
        print("\n📁 CREATING DEPLOYMENT FILES...")
        self.create_buildozer_spec()
        self.create_main_app_file()
        self.create_requirements_file()
        
        self.show_build_commands()
        self.show_installation_guide()
        self.show_troubleshooting()
        self.show_optimization_tips()
        
        print("\n🎉 DEPLOYMENT GUIDE COMPLETE!")
        print("=" * 40)
        print("📋 QUICK START CHECKLIST:")
        print("□ Install dependencies (see commands above)")
        print("□ Run: buildozer android debug")
        print("□ Wait for build to complete (30-60 min first time)")
        print("□ Install APK on phone")
        print("□ Test app functionality")
        print()
        print("📱 Your APK will be in: bin/cryptotradingassistant-1.0-debug.apk")
        print("🚀 Ready to trade on mobile!")

if __name__ == "__main__":
    guide = AndroidDeploymentGuide()
    guide.run_complete_guide()
