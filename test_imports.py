#!/usr/bin/env python3
# Test script to verify all imports work before building APK

print("🧪 TESTING MOBILE TRADING APP IMPORTS")
print("=" * 50)

try:
    print("📱 Testing main app import...")
    from mobile_trading_ui import MobileTradingApp
    print("✅ mobile_trading_ui imported successfully")
    
    print("🎯 Testing position manager import...")
    from position_manager import PositionManager, PositionStatus
    print("✅ position_manager imported successfully")
    
    print("📊 Testing trading pairs import...")
    from mobile_trading_pairs import MobileTradingPairs, TIER_1_PAIRS
    print("✅ mobile_trading_pairs imported successfully")
    print(f"📈 Found {len(TIER_1_PAIRS)} tier 1 trading pairs")
    
    print("\n🎉 ALL IMPORTS SUCCESSFUL!")
    print("✅ Your mobile trading app is ready to build")
    print("\n🚀 Key features verified:")
    print(f"   📱 Mobile UI: {MobileTradingApp.__name__}")
    print(f"   🤖 Position Manager: {PositionManager.__name__}")
    print(f"   📊 Trading Pairs: {len(TIER_1_PAIRS)} pairs configured")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("🔧 Fix this import error before building APK")
    exit(1)
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
    exit(1)

print("\n✅ All systems ready for APK build!")
