[app]

# Basic app information
title = Crypto Trading Assistant
package.name = cryptotradingassistant
package.domain = com.yourname.cryptotrading

# Source code
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json

# Version info
version = 1.0
#version.regex = __version__ = ['"](.+)['"]
#version.filename = %(source.dir)s/main.py

# Application requirements
requirements = python3,kivy==2.3.1,plyer,requests,websocket-client,pandas,numpy,cython

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
