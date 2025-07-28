# Mobile Trading App - Complete Buy/Sell Demo
"""
COMPREHENSIVE MOBILE TRADING SYSTEM DEMO

This demonstrates the complete user flow:
1. User sees trading pairs with signals
2. Strong signals generate BUY/SELL suggestions
3. User can accept suggestions to enter positions
4. App monitors positions and alerts on exit conditions
5. Automatic stop-loss, take-profit, and trailing stops
"""

import time
import random
from datetime import datetime
from mobile_trading_pairs import MobileTradingPairs, TIER_1_PAIRS
from position_manager import PositionManager, PositionStatus

class MobileTradingDemo:
    """Complete mobile trading demo showing buy/sell workflow"""
    
    def __init__(self):
        self.position_manager = PositionManager()
        self.trading_pairs = MobileTradingPairs()
        self.active_pairs = TIER_1_PAIRS[:8]  # Monitor top 8 pairs
        
    def simulate_market_data(self, symbol):
        """Simulate realistic market data for a symbol"""
        base_prices = {
            'BTC/USDT': 45000,
            'ETH/USDT': 2800,
            'SOL/USDT': 95,
            'ADA/USDT': 0.45,
            'DOT/USDT': 8.5,
            'MATIC/USDT': 0.95,
            'LINK/USDT': 15.2,
            'AVAX/USDT': 38.5
        }
        
        base_price = base_prices.get(symbol, 100)
        
        # Add some volatility
        price = base_price * (1 + random.uniform(-0.05, 0.05))
        change_pct = random.uniform(-8, 8)
        
        # Generate signal strength based on change and randomness
        signal_strength = change_pct * 12 + random.uniform(-30, 30)  # More volatile signals
        signal_strength = max(-100, min(100, signal_strength))
        
        # Boost some signals randomly for demo
        if random.random() < 0.3:  # 30% chance of strong signal
            signal_strength = signal_strength * 1.5
            signal_strength = max(-100, min(100, signal_strength))
        
        return price, change_pct, signal_strength
    
    def check_for_suggestions(self):
        """Check all pairs for trading suggestions"""
        print("🔍 SCANNING FOR TRADING OPPORTUNITIES...")
        print("-" * 50)
        
        suggestions_created = 0
        
        for symbol in self.active_pairs:
            # Skip if already have suggestion or position
            if (symbol in self.position_manager.suggested_positions or 
                symbol in self.position_manager.active_positions):
                continue
                
            price, change_pct, signal_strength = self.simulate_market_data(symbol)
            
            print(f"📊 {symbol:12} | ${price:8.2f} | {change_pct:+5.1f}% | Signal: {signal_strength:+5.0f}")
            
            # Create suggestion for strong signals
            if abs(signal_strength) > 75:
                signal_data = {
                    'symbol': symbol,
                    'signal_type': 'BUY' if signal_strength > 0 else 'SELL',
                    'price': price,
                    'strength': abs(signal_strength),
                    'timestamp': datetime.now()
                }
                
                suggestion = self.position_manager.suggest_position(symbol, signal_data)
                
                print(f"💡 SUGGESTION: {suggestion.signal_type} {symbol} at ${price:.2f}")
                print(f"   Stop: ${suggestion.stop_loss:.2f} | Target: ${suggestion.take_profit:.2f}")
                print(f"   Risk/Reward: {suggestion.risk_reward_ratio:.1f}:1 | Confidence: {suggestion.confidence}%")
                
                suggestions_created += 1
        
        print(f"\n✨ Created {suggestions_created} new suggestions")
        return suggestions_created
    
    def show_user_suggestions(self):
        """Show suggestions to user for decision"""
        suggestions = self.position_manager.get_position_suggestions()
        
        if not suggestions:
            print("💤 No suggestions available")
            return
        
        print(f"\n🎯 YOU HAVE {len(suggestions)} TRADING SUGGESTIONS:")
        print("=" * 60)
        
        for i, suggestion in enumerate(suggestions, 1):
            profit_potential = suggestion.take_profit - suggestion.entry_price
            if suggestion.signal_type == "SELL":
                profit_potential = suggestion.entry_price - suggestion.take_profit
            
            print(f"[{i}] 🚀 {suggestion.signal_type} {suggestion.symbol}")
            print(f"    Entry: ${suggestion.entry_price:.2f}")
            print(f"    Stop Loss: ${suggestion.stop_loss:.2f}")
            print(f"    Take Profit: ${suggestion.take_profit:.2f}")
            print(f"    Position Size: ${suggestion.position_size:.2f}")
            print(f"    Max Profit: ${profit_potential:.2f}")
            print(f"    Risk/Reward: {suggestion.risk_reward_ratio:.1f}:1")
            print(f"    Confidence: {suggestion.confidence}%")
            print()
        
        return suggestions
    
    def simulate_user_decisions(self, suggestions):
        """Simulate user accepting/declining suggestions"""
        print("🤔 USER MAKING DECISIONS...")
        print("-" * 30)
        
        for suggestion in suggestions:
            # Higher confidence = higher chance of acceptance
            accept_probability = suggestion.confidence / 100 * 0.7  # 70% max acceptance rate
            
            if random.random() < accept_probability:
                print(f"✅ USER ACCEPTS: {suggestion.symbol} {suggestion.signal_type}")
                self.position_manager.accept_suggestion(suggestion.symbol)
            else:
                print(f"❌ USER DECLINES: {suggestion.symbol} {suggestion.signal_type}")
    
    def monitor_active_positions(self):
        """Monitor and update active positions"""
        active_positions = self.position_manager.get_active_positions()
        
        if not active_positions:
            print("💤 No active positions to monitor")
            return
        
        print(f"\n📈 MONITORING {len(active_positions)} ACTIVE POSITIONS:")
        print("=" * 70)
        
        for position in active_positions:
            # Simulate price movement
            price_change = random.uniform(-0.03, 0.03)  # ±3% movement
            new_price = position.current_price * (1 + price_change)
            
            # Update position
            result = self.position_manager.update_position(position.symbol, new_price)
            
            updated_position = result['position']
            if updated_position:
                status_color = "🟢" if updated_position.profit_loss > 0 else "🔴"
                
                print(f"{status_color} {updated_position.symbol:12} | "
                      f"Entry: ${updated_position.entry_price:8.2f} | "
                      f"Current: ${updated_position.current_price:8.2f} | "
                      f"P&L: ${updated_position.profit_loss:8.2f} ({updated_position.profit_pct:+5.1f}%)")
                
                # Show any alerts
                for alert in result['alerts']:
                    print(f"   🔔 {alert}")
    
    def show_portfolio_summary(self):
        """Show portfolio performance summary"""
        summary = self.position_manager.get_portfolio_summary()
        
        print(f"\n💼 PORTFOLIO SUMMARY:")
        print("=" * 40)
        print(f"🔄 Active Positions: {summary['active_positions']}")
        print(f"💡 Pending Suggestions: {summary['suggested_positions']}")
        print(f"💰 Total Portfolio Value: ${summary['total_portfolio_value']:.2f}")
        print(f"📊 Unrealized P&L: ${summary['unrealized_pnl']:.2f}")
        print(f"📈 30-Day Performance: ${summary['total_pnl_30d']:.2f}")
        print(f"🎯 30-Day Win Rate: {summary['win_rate_30d']:.1f}%")
        print(f"🟢 Winning Positions: {summary['winning_positions']}")
        print(f"🔴 Losing Positions: {summary['losing_positions']}")
    
    def run_demo(self, cycles=5):
        """Run complete trading demo"""
        print("🚀 MOBILE TRADING APP - BUY/SELL RECOMMENDATION DEMO")
        print("=" * 60)
        print("This demo shows the complete user experience:")
        print("1. 🔍 Scan for trading opportunities")
        print("2. 💡 Generate BUY/SELL suggestions")
        print("3. ✅ User accepts/declines suggestions")
        print("4. 📈 Monitor active positions")
        print("5. 🔔 Alert on exit conditions")
        print("6. 💼 Track portfolio performance")
        print("=" * 60)
        
        for cycle in range(1, cycles + 1):
            print(f"\n🔄 CYCLE {cycle}/{cycles}")
            print("=" * 40)
            
            # Step 1: Scan for opportunities
            self.check_for_suggestions()
            
            # Step 2: Show suggestions to user
            suggestions = self.show_user_suggestions()
            
            # Step 3: User makes decisions
            if suggestions:
                self.simulate_user_decisions(suggestions)
            
            # Step 4: Monitor active positions
            self.monitor_active_positions()
            
            # Step 5: Show portfolio summary
            self.show_portfolio_summary()
            
            if cycle < cycles:
                print(f"\n⏱️  Waiting for next cycle...")
                time.sleep(2)  # Brief pause for demo
        
        print(f"\n🏁 DEMO COMPLETE!")
        self.show_final_summary()
    
    def show_final_summary(self):
        """Show final demo summary"""
        print("\n📊 FINAL DEMO SUMMARY:")
        print("=" * 50)
        
        all_positions = (self.position_manager.get_active_positions() + 
                        self.position_manager.position_history)
        
        if all_positions:
            total_trades = len(all_positions)
            profitable_trades = sum(1 for p in all_positions if p.profit_loss > 0)
            total_pnl = sum(p.profit_loss for p in all_positions)
            
            print(f"📈 Total Trades: {total_trades}")
            print(f"🎯 Profitable Trades: {profitable_trades}")
            print(f"📊 Win Rate: {profitable_trades/total_trades*100:.1f}%")
            print(f"💰 Total P&L: ${total_pnl:.2f}")
            
            print(f"\n🎉 The mobile app successfully:")
            print(f"   ✅ Generated intelligent trade suggestions")
            print(f"   ✅ Managed risk with stop-losses")
            print(f"   ✅ Monitored positions automatically")
            print(f"   ✅ Alerted users on exit conditions")
            print(f"   ✅ Tracked portfolio performance")
        else:
            print("💤 No trades were executed in this demo")
        
        print(f"\n📱 READY FOR MOBILE DEPLOYMENT!")

if __name__ == "__main__":
    # Run the complete mobile trading demo
    demo = MobileTradingDemo()
    demo.run_demo(cycles=3)
