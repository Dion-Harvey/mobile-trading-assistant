#!/usr/bin/env python3
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
        print("Starting Crypto Trading Assistant...")
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
