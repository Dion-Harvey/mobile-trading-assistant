#!/usr/bin/env python3
"""
Quick Start Trading Bot - Minimal Dependencies Version
This version works without TA-Lib while you get it installed
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
import ccxt
import requests
import threading
import time
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleTechnicalAnalyzer:
    """Simplified technical analyzer without TA-Lib dependency"""
    
    def __init__(self):
        self.indicators = {}
    
    def simple_rsi(self, prices, period=14):
        """Calculate RSI without TA-Lib"""
        deltas = np.diff(prices)
        gain = np.where(deltas > 0, deltas, 0)
        loss = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gain[:period])
        avg_loss = np.mean(loss[:period])
        
        rs = avg_gain / avg_loss if avg_loss != 0 else 100
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def simple_sma(self, prices, period):
        """Simple Moving Average"""
        return np.mean(prices[-period:])
    
    def simple_ema(self, prices, period):
        """Exponential Moving Average"""
        multiplier = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        return ema
    
    def calculate_basic_indicators(self, df):
        """Calculate basic indicators without TA-Lib"""
        if len(df) < 50:
            return {}
        
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values
        
        indicators = {}
        
        # Basic price indicators
        indicators['current_price'] = close[-1]
        indicators['price_change'] = close[-1] - close[-2] if len(close) > 1 else 0
        indicators['price_change_pct'] = (indicators['price_change'] / close[-2] * 100) if len(close) > 1 and close[-2] != 0 else 0
        
        # Simple RSI
        if len(close) >= 14:
            indicators['rsi'] = self.simple_rsi(close)
            indicators['rsi_oversold'] = indicators['rsi'] < 30
            indicators['rsi_overbought'] = indicators['rsi'] > 70
        
        # Moving averages
        if len(close) >= 20:
            indicators['sma_20'] = self.simple_sma(close, 20)
            indicators['ema_20'] = self.simple_ema(close, 20)
            indicators['price_above_sma20'] = close[-1] > indicators['sma_20']
            indicators['price_above_ema20'] = close[-1] > indicators['ema_20']
        
        # Volume analysis
        if len(volume) >= 20:
            avg_volume_20 = np.mean(volume[-20:])
            indicators['current_volume'] = volume[-1]
            indicators['avg_volume'] = avg_volume_20
            indicators['volume_ratio'] = volume[-1] / avg_volume_20
            indicators['volume_surge'] = volume[-1] > (avg_volume_20 * 2)
            indicators['volume_spike_3x'] = volume[-1] > (avg_volume_20 * 3)
            indicators['volume_spike_5x'] = volume[-1] > (avg_volume_20 * 5)
        
        # High/Low analysis
        indicators['daily_high'] = np.max(high[-20:]) if len(high) >= 20 else high[-1]
        indicators['daily_low'] = np.min(low[-20:]) if len(low) >= 20 else low[-1]
        indicators['near_high'] = close[-1] > (indicators['daily_high'] * 0.95)
        indicators['near_low'] = close[-1] < (indicators['daily_low'] * 1.05)
        
        return indicators

class SimpleSignalGenerator:
    """Simplified signal generator"""
    
    def __init__(self):
        self.analyzer = SimpleTechnicalAnalyzer()
    
    def generate_simple_signals(self, symbol: str, data: Dict[str, pd.DataFrame]) -> List:
        """Generate basic trading signals"""
        signals = []
        
        try:
            df = data.get('5m')
            if df is None or len(df) < 20:
                print(f"⚠️  Not enough data for {symbol}: {len(df) if df is not None else 0} bars")
                return signals
            
            indicators = self.analyzer.calculate_basic_indicators(df)
            print(f"🔍 Analyzing {symbol}: RSI={indicators.get('rsi', 0):.1f}, Volume Ratio={indicators.get('volume_ratio', 0):.1f}x")
            
            # Simple bullish signal
            score = 0
            factors = []
            
            # RSI conditions (more lenient for demo)
            if indicators.get('rsi_oversold', False):
                score += 25
                factors.append("RSI_OVERSOLD")
            elif indicators.get('rsi', 50) > 40 and indicators.get('rsi', 50) < 70:
                score += 15
                factors.append("RSI_BULLISH")
            
            # Volume surge detection (key for day trading)
            volume_ratio = indicators.get('volume_ratio', 1)
            if volume_ratio > 3:
                score += 30
                factors.append(f"VOLUME_SURGE_{volume_ratio:.1f}X")
            elif volume_ratio > 2:
                score += 20
                factors.append(f"VOLUME_SPIKE_{volume_ratio:.1f}X")
            elif volume_ratio > 1.5:
                score += 10
                factors.append(f"VOLUME_UP_{volume_ratio:.1f}X")
            
            # Price above moving averages
            if indicators.get('price_above_sma20', False):
                score += 10
                factors.append("ABOVE_SMA20")
            if indicators.get('price_above_ema20', False):
                score += 10
                factors.append("ABOVE_EMA20")
            
            # Price momentum
            price_change = indicators.get('price_change_pct', 0)
            if price_change > 2:
                score += 15
                factors.append(f"MOMENTUM_+{price_change:.1f}%")
            elif price_change > 0:
                score += 5
                factors.append(f"POSITIVE_{price_change:.1f}%")
            
            # Generate signal if score is decent (lowered threshold for demo)
            if score >= 25:  # Lowered from 40 to show more signals
                current_price = indicators.get('current_price', 0)
                signal = {
                    'symbol': symbol,
                    'signal_type': 'BUY',
                    'strength': min(score, 100),
                    'price': current_price,
                    'factors': factors,
                    'timestamp': datetime.now(),
                    'confidence': 'HIGH' if score >= 60 else 'MEDIUM' if score >= 40 else 'LOW'
                }
                signals.append(signal)
                print(f"🚨 SIGNAL GENERATED: {symbol} BUY {score}% - {', '.join(factors)}")
            
            # Also check for bearish signals
            bear_score = 0
            bear_factors = []
            
            if indicators.get('rsi_overbought', False):
                bear_score += 25
                bear_factors.append("RSI_OVERBOUGHT")
            
            if price_change < -2:
                bear_score += 20
                bear_factors.append(f"DECLINE_{abs(price_change):.1f}%")
            
            if volume_ratio > 2 and price_change < -1:
                bear_score += 25
                bear_factors.append("HIGH_VOL_SELLING")
            
            if bear_score >= 25:
                current_price = indicators.get('current_price', 0)
                signal = {
                    'symbol': symbol,
                    'signal_type': 'SELL',
                    'strength': min(bear_score, 100),
                    'price': current_price,
                    'factors': bear_factors,
                    'timestamp': datetime.now(),
                    'confidence': 'HIGH' if bear_score >= 60 else 'MEDIUM' if bear_score >= 40 else 'LOW'
                }
                signals.append(signal)
                print(f"🔴 SIGNAL GENERATED: {symbol} SELL {bear_score}% - {', '.join(bear_factors)}")
                
        except Exception as e:
            print(f"Error generating signals for {symbol}: {e}")
            
        return signals

class SimpleTradingBot:
    """Simplified trading bot without TA-Lib"""
    
    def __init__(self):
        self.running = False
        self.exchange = None
        self.signal_generator = SimpleSignalGenerator()
        # Expanded list of trading pairs for better coverage
        self.symbols = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
            'XRP/USDT', 'DOT/USDT', 'AVAX/USDT', 'MATIC/USDT', 'LINK/USDT',
            'UNI/USDT', 'LTC/USDT', 'ALGO/USDT', 'ATOM/USDT', 'VET/USDT'
        ]
        self.price_data = {}
        self.latest_signals = {}
        self.signal_count = 0
        
        # Initialize exchange (using real data, not sandbox)
        try:
            self.exchange = ccxt.binanceus({
                'rateLimit': 1200,
                'enableRateLimit': True,
            })
            print("✅ Exchange connection established")
        except Exception as e:
            logger.error(f"Error initializing exchange: {e}")
            print(f"⚠️  Exchange error: {e}")
    
    def setup_gui(self):
        """Setup simple GUI"""
        self.root = tk.Tk()
        self.root.title("🚀 Simple Trading Bot - Live Market Data")
        self.root.geometry("1000x700")
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="🚀 SIMPLE TRADING BOT - LIVE DATA", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="🟢 READY TO MONITOR MARKETS", font=('Arial', 12), foreground="green")
        self.status_label.pack(pady=5)
        
        # Market Data Frame
        market_frame = ttk.LabelFrame(main_frame, text="Live Market Data", padding="10")
        market_frame.pack(fill='x', pady=10)
        
        # Create market display variables
        self.market_vars = {}
        for i, symbol in enumerate(self.symbols):
            symbol_frame = ttk.Frame(market_frame)
            symbol_frame.pack(fill='x', pady=2)
            
            # Symbol
            symbol_label = ttk.Label(symbol_frame, text=f"{symbol}:", font=('Arial', 10, 'bold'), width=12)
            symbol_label.pack(side='left')
            
            # Price
            price_var = tk.StringVar(value="Loading price...")
            price_label = ttk.Label(symbol_frame, textvariable=price_var, width=20)
            price_label.pack(side='left', padx=5)
            
            # Volume
            volume_var = tk.StringVar(value="Loading volume...")
            volume_label = ttk.Label(symbol_frame, textvariable=volume_var, width=20)
            volume_label.pack(side='left', padx=5)
            
            # Signal
            signal_var = tk.StringVar(value="No signal yet")
            signal_label = ttk.Label(symbol_frame, textvariable=signal_var, width=25)
            signal_label.pack(side='left', padx=5)
            
            self.market_vars[symbol] = {
                'price': price_var,
                'volume': volume_var, 
                'signal': signal_var,
                'signal_label': signal_label
            }
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        self.start_button = ttk.Button(button_frame, text="▶️ Start Monitoring", command=self.start_monitoring)
        self.start_button.pack(side='left', padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop", command=self.stop_monitoring, state='disabled')
        self.stop_button.pack(side='left', padx=5)
        
        self.test_button = ttk.Button(button_frame, text="🧪 Test Connection", command=self.test_connection)
        self.test_button.pack(side='left', padx=5)
        
        # Signals display
        signals_label = ttk.Label(main_frame, text="Recent Signals:", font=('Arial', 12, 'bold'))
        signals_label.pack(pady=(20, 5))
        
        # Instructions for user
        instructions = ttk.Label(main_frame, 
                                text="👆 Click 'Start Monitoring' to begin signal generation\n"
                                     "🎯 Monitoring 15 trading pairs for opportunities\n"
                                     "⚡ Signals will appear below when detected",
                                font=('Arial', 10), 
                                foreground='blue')
        instructions.pack(pady=5)
        
        # Create treeview for signals
        columns = ('Time', 'Symbol', 'Direction', 'Strength', 'Confidence', 'Price')
        self.signals_tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.signals_tree.heading(col, text=col)
            self.signals_tree.column(col, width=120)
        
        self.signals_tree.pack(fill='both', expand=True, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.signals_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.signals_tree.configure(yscrollcommand=scrollbar.set)
        
        # Immediately test connection and load initial data
        self.root.after(1000, self.test_connection)  # Test after 1 second
    
    def test_connection(self):
        """Test exchange connection and load initial market data"""
        try:
            self.status_label.config(text="🔄 Testing connection...", foreground="orange")
            self.root.update()
            
            if not self.exchange:
                self.status_label.config(text="❌ No exchange connection", foreground="red")
                return
            
            # Test with one symbol first
            test_symbol = 'BTC/USDT'
            ticker = self.exchange.fetch_ticker(test_symbol)
            
            if ticker:
                self.status_label.config(text="✅ Connection successful! Loading market data...", foreground="green")
                print(f"✅ Successfully connected! BTC price: ${ticker['last']:,.2f}")
                
                # Load initial data for all symbols
                for symbol in self.symbols:
                    try:
                        self.update_market_display(symbol)
                    except Exception as e:
                        print(f"⚠️  Error loading {symbol}: {e}")
                
                self.status_label.config(text="🟢 Ready to start monitoring", foreground="green")
            else:
                self.status_label.config(text="❌ Connection test failed", foreground="red")
                
        except Exception as e:
            error_msg = f"❌ Connection error: {str(e)[:50]}..."
            self.status_label.config(text=error_msg, foreground="red")
            print(f"Connection error: {e}")
    
    def update_market_display(self, symbol):
        """Update market display for a symbol"""
        try:
            # Get current price data
            ticker = self.exchange.fetch_ticker(symbol)
            
            if symbol in self.market_vars:
                # Update price
                price = ticker['last']
                change_pct = ticker.get('percentage', 0) or 0
                price_color = "green" if change_pct >= 0 else "red"
                price_text = f"${price:,.4f} ({change_pct:+.2f}%)"
                self.market_vars[symbol]['price'].set(price_text)
                
                # Update volume
                volume = ticker.get('baseVolume', 0) or 0
                volume_text = f"Vol: {volume:,.0f}"
                self.market_vars[symbol]['volume'].set(volume_text)
                
                # Initialize signal display
                self.market_vars[symbol]['signal'].set("Analyzing...")
                
                print(f"📊 {symbol}: ${price:,.4f} ({change_pct:+.2f}%) Vol: {volume:,.0f}")
                
        except Exception as e:
            if symbol in self.market_vars:
                self.market_vars[symbol]['price'].set("Error loading")
                self.market_vars[symbol]['volume'].set("Error loading")
            print(f"Error updating {symbol}: {e}")
    
    def start_monitoring(self):
        """Start monitoring markets"""
        self.running = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="Status: Monitoring markets... 🟢")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_markets, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Status: Stopped 🔴")
    
    def monitor_markets(self):
        """Monitor markets for signals"""
        while self.running:
            try:
                for symbol in self.symbols:
                    if not self.running:
                        break
                    
                    # Get market data
                    data = self.get_market_data(symbol)
                    if data:
                        # Generate signals
                        signals = self.signal_generator.generate_simple_signals(symbol, data)
                        
                        # Display signals
                        for signal in signals:
                            self.display_signal(signal)
                    
                    time.sleep(2)  # Avoid rate limits
                
                time.sleep(10)  # Wait before next cycle
                
            except Exception as e:
                logger.error(f"Error in monitoring: {e}")
                time.sleep(30)
    
    def get_market_data(self, symbol: str) -> Dict:
        """Get market data for symbol"""
        try:
            if not self.exchange:
                return None
            
            # Get 5-minute OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(symbol, '5m', limit=100)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return {'5m': df}
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def display_signal(self, signal):
        """Display signal in GUI"""
        try:
            self.root.after(0, self._insert_signal, signal)
        except Exception as e:
            logger.error(f"Error displaying signal: {e}")
    
    def _insert_signal(self, signal):
        """Insert signal into treeview (thread-safe)"""
        try:
            values = (
                signal['timestamp'].strftime('%H:%M:%S'),
                signal['symbol'],
                signal['signal_type'],
                f"{signal['strength']}/100",
                signal['confidence'],
                f"${signal['price']:.2f}"
            )
            
            self.signals_tree.insert('', 0, values=values)
            
            # Keep only last 50 signals
            items = self.signals_tree.get_children()
            if len(items) > 50:
                self.signals_tree.delete(items[-1])
                
        except Exception as e:
            logger.error(f"Error inserting signal: {e}")
    
    def run(self):
        """Run the bot"""
        self.setup_gui()
        self.root.mainloop()

def main():
    """Main function"""
    print("="*60)
    print("🚀 SIMPLE TRADING BOT - READY FOR DAY TRADING!")
    print("="*60)
    print("✅ This version works without TA-Lib")
    print("✅ Monitors volume surges and basic patterns")
    print("✅ Real-time signal generation")
    print("✅ Perfect for day trading!")
    print("="*60)
    
    try:
        bot = SimpleTradingBot()
        bot.run()
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
