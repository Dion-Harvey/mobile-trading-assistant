# Enhanced Trading Bot - Support for 50+ Trading Pairs

import asyncio
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from mobile_trading_pairs import MobileTradingPairs, TIER_1_PAIRS, TIER_2_PAIRS
import time

class EnhancedTradingBot:
    """Enhanced bot supporting 50+ trading pairs efficiently"""
    
    def __init__(self):
        self.mobile_config = MobileTradingPairs()
        self.all_pairs = self.mobile_config.all_pairs
        
        # Performance optimizations
        self.max_concurrent = 8           # Analyze 8 pairs simultaneously
        self.update_intervals = {
            'tier1': 5,                   # Update tier 1 every 5 seconds
            'tier2': 10,                  # Update tier 2 every 10 seconds  
            'tier3': 20,                  # Update tier 3 every 20 seconds
            'tier4': 30                   # Update tier 4 every 30 seconds
        }
        
        # Signal filtering for mobile
        self.signal_thresholds = {
            'critical': 80,               # Always notify
            'high': 65,                   # Notify if tier 1-2
            'medium': 50,                 # Notify if tier 1 only
            'low': 35                     # No mobile notifications
        }
        
        self.exchange = None
        self.signal_cache = {}
        self.last_updates = {}
        
    def get_pairs_by_priority(self):
        """Get trading pairs organized by update priority"""
        return {
            'tier1': TIER_1_PAIRS,                    # 10 pairs - High priority
            'tier2': TIER_2_PAIRS,                    # 15 pairs - Medium priority  
            'tier3': self.mobile_config.get_pairs_by_tier("tier3")[25:40],  # 15 pairs - Lower priority
            'tier4': self.mobile_config.get_pairs_by_tier("all")[40:50]     # 10 pairs - Lowest priority
        }
    
    def should_update_tier(self, tier: str) -> bool:
        """Check if tier needs updating based on intervals"""
        current_time = time.time()
        last_update = self.last_updates.get(tier, 0)
        interval = self.update_intervals[tier]
        
        return (current_time - last_update) >= interval
    
    async def analyze_pairs_async(self, pairs_list: list) -> dict:
        """Analyze multiple pairs asynchronously"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            # Create tasks for each pair
            future_to_pair = {
                executor.submit(self.analyze_single_pair, pair): pair 
                for pair in pairs_list
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_pair):
                pair = future_to_pair[future]
                try:
                    result = future.result(timeout=10)  # 10 second timeout per pair
                    if result:
                        results[pair] = result
                except Exception as e:
                    print(f"❌ Error analyzing {pair}: {e}")
                    
        return results
    
    def analyze_single_pair(self, symbol: str) -> dict:
        """Analyze a single trading pair (your existing logic)"""
        try:
            # Simulate getting market data (replace with your real logic)
            # This would use your existing SimpleTechnicalAnalyzer
            
            # Mock data for demonstration
            import random
            
            analysis = {
                'symbol': symbol,
                'price': random.uniform(0.1, 50000),
                'change_pct': random.uniform(-10, 10),
                'volume_ratio': random.uniform(0.5, 8.0),
                'rsi': random.uniform(10, 90),
                'signal_strength': random.uniform(0, 100),
                'signal_type': 'BUY' if random.random() > 0.5 else 'SELL',
                'timestamp': time.time()
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None
    
    def filter_signals_for_mobile(self, analysis_results: dict) -> dict:
        """Filter signals for mobile notifications"""
        mobile_signals = {}
        
        for symbol, data in analysis_results.items():
            strength = data.get('signal_strength', 0)
            
            # Determine tier
            if symbol in TIER_1_PAIRS:
                tier = 'tier1'
            elif symbol in TIER_2_PAIRS:
                tier = 'tier2'
            else:
                tier = 'tier3+'
            
            # Apply mobile filtering
            should_notify = False
            
            if strength >= self.signal_thresholds['critical']:
                should_notify = True
                priority = 'critical'
            elif strength >= self.signal_thresholds['high'] and tier in ['tier1', 'tier2']:
                should_notify = True
                priority = 'high'
            elif strength >= self.signal_thresholds['medium'] and tier == 'tier1':
                should_notify = True
                priority = 'medium'
            
            if should_notify:
                mobile_signals[symbol] = {
                    **data,
                    'priority': priority,
                    'tier': tier
                }
        
        return mobile_signals
    
    async def monitor_all_pairs(self):
        """Main monitoring loop for all pairs"""
        pairs_by_priority = self.get_pairs_by_priority()
        
        while True:
            current_time = time.time()
            all_results = {}
            
            # Check each tier and update if needed
            for tier, pairs in pairs_by_priority.items():
                if self.should_update_tier(tier):
                    print(f"🔄 Updating {tier}: {len(pairs)} pairs")
                    
                    # Analyze pairs in this tier
                    tier_results = await self.analyze_pairs_async(pairs)
                    all_results.update(tier_results)
                    
                    # Update last update time
                    self.last_updates[tier] = current_time
                    
                    print(f"✅ {tier} updated: {len(tier_results)} results")
            
            # Filter for mobile notifications
            if all_results:
                mobile_signals = self.filter_signals_for_mobile(all_results)
                
                if mobile_signals:
                    print(f"📱 Mobile Signals: {len(mobile_signals)}")
                    for symbol, signal in mobile_signals.items():
                        print(f"  🚨 {symbol}: {signal['signal_type']} {signal['signal_strength']:.0f}% ({signal['priority']})")
            
            # Wait before next iteration
            await asyncio.sleep(2)  # Check every 2 seconds
    
    def get_mobile_dashboard_data(self) -> dict:
        """Get data optimized for mobile dashboard"""
        return {
            'total_pairs_monitored': len(self.all_pairs),
            'tier1_pairs': len(TIER_1_PAIRS),
            'tier2_pairs': len(TIER_2_PAIRS),
            'active_signals': len(self.signal_cache),
            'last_update': max(self.last_updates.values()) if self.last_updates else 0,
            'performance': {
                'pairs_per_second': len(self.all_pairs) / 30,  # Rough estimate
                'memory_efficient': True,
                'battery_optimized': True
            }
        }

# Mobile-specific optimizations
class MobileOptimizer:
    """Optimize bot performance for mobile devices"""
    
    @staticmethod
    def reduce_battery_usage():
        """Optimize for battery life"""
        return {
            'background_scan_interval': 30,      # Slower background scans
            'screen_off_monitoring': 'tier1_only',  # Only monitor favorites when screen off
            'push_notifications_only': True,     # Don't update UI in background
            'wifi_only_updates': False,          # Allow cellular updates
            'low_power_mode': True               # Reduce computation intensity
        }
    
    @staticmethod
    def optimize_memory():
        """Optimize memory usage"""
        return {
            'max_historical_data': 100,          # Limit historical candles
            'compress_data': True,               # Compress cached data
            'clear_old_signals': 300,            # Clear signals older than 5 minutes
            'lazy_load_pairs': True,             # Only load visible pairs
            'max_concurrent_requests': 5        # Limit concurrent API calls
        }

# Usage example
async def main():
    """Example of running enhanced bot with 50+ pairs"""
    print("🚀 Starting Enhanced Trading Bot")
    print("📱 Mobile-optimized for 50+ trading pairs")
    
    bot = EnhancedTradingBot()
    mobile_optimizer = MobileOptimizer()
    
    # Apply mobile optimizations
    battery_settings = mobile_optimizer.reduce_battery_usage()
    memory_settings = mobile_optimizer.optimize_memory()
    
    print(f"⚡ Battery optimizations: {battery_settings}")
    print(f"💾 Memory optimizations: {memory_settings}")
    
    dashboard_data = bot.get_mobile_dashboard_data()
    print(f"📊 Dashboard: {dashboard_data}")
    
    # Start monitoring (comment out for demo)
    # await bot.monitor_all_pairs()

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
