# Mobile Trading App - Buy/Sell Recommendation & Monitoring System

from datetime import datetime, timedelta
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from enum import Enum

class PositionStatus(Enum):
    SUGGESTED = "suggested"
    WATCHING = "watching"
    ENTERED = "entered"
    PROFIT_TARGET = "profit_target"
    STOP_LOSS = "stop_loss"
    MANUAL_EXIT = "manual_exit"
    EXPIRED = "expired"

@dataclass
class TradingPosition:
    """Represents a trading position suggestion or active trade"""
    symbol: str
    signal_type: str          # BUY/SELL
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    position_size: float      # Dollar amount or percentage
    confidence: int           # 0-100
    status: PositionStatus
    entry_time: datetime
    exit_time: Optional[datetime] = None
    profit_loss: float = 0.0
    profit_pct: float = 0.0
    risk_reward_ratio: float = 0.0
    trailing_stop: Optional[float] = None
    alerts_sent: List[str] = None
    
    def __post_init__(self):
        if self.alerts_sent is None:
            self.alerts_sent = []
        self.calculate_metrics()
    
    def calculate_metrics(self):
        """Calculate position metrics"""
        if self.signal_type == "BUY":
            self.profit_loss = (self.current_price - self.entry_price) * self.position_size
            self.profit_pct = ((self.current_price - self.entry_price) / self.entry_price) * 100
        else:  # SELL/SHORT
            self.profit_loss = (self.entry_price - self.current_price) * self.position_size
            self.profit_pct = ((self.entry_price - self.current_price) / self.entry_price) * 100
        
        # Risk/Reward calculation
        if self.signal_type == "BUY":
            risk = abs(self.entry_price - self.stop_loss)
            reward = abs(self.take_profit - self.entry_price)
        else:
            risk = abs(self.stop_loss - self.entry_price)
            reward = abs(self.entry_price - self.take_profit)
        
        self.risk_reward_ratio = reward / risk if risk > 0 else 0

class PositionManager:
    """Manages trading position suggestions and monitoring"""
    
    def __init__(self):
        self.active_positions = {}  # symbol -> TradingPosition
        self.suggested_positions = {}  # symbol -> TradingPosition
        self.position_history = []
        self.user_preferences = self.load_user_preferences()
        
    def load_user_preferences(self) -> Dict:
        """Load user trading preferences"""
        # In real app, this would load from user settings
        return {
            'risk_tolerance': 'medium',    # low, medium, high
            'max_positions': 5,            # Maximum concurrent positions
            'default_position_size': 100,  # Default dollar amount
            'auto_stop_loss': True,        # Automatically set stop losses
            'trailing_stops': True,        # Use trailing stops
            'profit_target_method': 'risk_reward',  # risk_reward, percentage, technical
            'notification_preferences': {
                'entry_signals': True,
                'exit_alerts': True,
                'profit_targets': True,
                'stop_losses': True,
                'daily_summary': True
            }
        }
    
    def suggest_position(self, symbol: str, signal_data: Dict) -> TradingPosition:
        """Create a position suggestion based on signal"""
        entry_price = signal_data['price']
        signal_type = signal_data['signal_type']
        confidence = signal_data['strength']
        
        # Calculate stop loss and take profit based on signal and risk tolerance
        stop_loss, take_profit = self._calculate_levels(
            entry_price, signal_type, signal_data, confidence
        )
        
        # Determine position size based on risk tolerance and confidence
        position_size = self._calculate_position_size(confidence, entry_price, stop_loss)
        
        position = TradingPosition(
            symbol=symbol,
            signal_type=signal_type,
            entry_price=entry_price,
            current_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            confidence=confidence,
            status=PositionStatus.SUGGESTED,
            entry_time=datetime.now()
        )
        
        # Store suggestion
        self.suggested_positions[symbol] = position
        
        return position
    
    def _calculate_levels(self, entry_price: float, signal_type: str, 
                         signal_data: Dict, confidence: int) -> tuple:
        """Calculate stop loss and take profit levels"""
        
        # Base percentages based on confidence and risk tolerance
        risk_tolerance = self.user_preferences['risk_tolerance']
        
        if risk_tolerance == 'low':
            base_stop_pct = 0.02    # 2% stop loss
            base_target_pct = 0.04  # 2:1 risk/reward
        elif risk_tolerance == 'medium':
            base_stop_pct = 0.03    # 3% stop loss
            base_target_pct = 0.09  # 3:1 risk/reward
        else:  # high
            base_stop_pct = 0.05    # 5% stop loss
            base_target_pct = 0.15  # 3:1 risk/reward
        
        # Adjust based on confidence (higher confidence = wider targets)
        confidence_multiplier = confidence / 100
        target_multiplier = 1 + confidence_multiplier
        
        if signal_type == "BUY":
            stop_loss = entry_price * (1 - base_stop_pct)
            take_profit = entry_price * (1 + (base_target_pct * target_multiplier))
        else:  # SELL
            stop_loss = entry_price * (1 + base_stop_pct)
            take_profit = entry_price * (1 - (base_target_pct * target_multiplier))
        
        return stop_loss, take_profit
    
    def _calculate_position_size(self, confidence: int, entry_price: float, stop_loss: float) -> float:
        """Calculate position size based on risk management"""
        base_size = self.user_preferences['default_position_size']
        
        # Risk per trade (percentage of account)
        risk_tolerance = self.user_preferences['risk_tolerance']
        if risk_tolerance == 'low':
            risk_per_trade = 0.01    # 1% of account
        elif risk_tolerance == 'medium':
            risk_per_trade = 0.02    # 2% of account
        else:
            risk_per_trade = 0.03    # 3% of account
        
        # Calculate position size based on stop loss distance
        stop_distance = abs(entry_price - stop_loss) / entry_price
        if stop_distance > 0:
            # Position size = (Risk per trade) / (Stop distance)
            calculated_size = (base_size * risk_per_trade) / stop_distance
            return min(calculated_size, base_size * 2)  # Cap at 2x base size
        
        return base_size
    
    def accept_suggestion(self, symbol: str) -> bool:
        """User accepts a position suggestion"""
        if symbol not in self.suggested_positions:
            return False
        
        position = self.suggested_positions[symbol]
        position.status = PositionStatus.ENTERED
        
        # Move to active positions
        self.active_positions[symbol] = position
        del self.suggested_positions[symbol]
        
        # Send entry confirmation
        self._send_alert(f"✅ Entered {symbol} {position.signal_type} at ${position.entry_price:.4f}")
        
        return True
    
    def update_position(self, symbol: str, current_price: float) -> Dict:
        """Update position with current market price and check exit conditions"""
        alerts = []
        
        if symbol in self.active_positions:
            position = self.active_positions[symbol]
            position.current_price = current_price
            position.calculate_metrics()
            
            # Check exit conditions
            exit_reason = self._check_exit_conditions(position)
            
            if exit_reason:
                alerts.extend(self._handle_position_exit(position, exit_reason))
            else:
                # Update trailing stop if enabled
                if self.user_preferences['trailing_stops']:
                    alerts.extend(self._update_trailing_stop(position))
                
                # Check for profit/loss milestones
                alerts.extend(self._check_milestones(position))
        
        return {
            'alerts': alerts,
            'position': self.active_positions.get(symbol),
            'status': 'updated'
        }
    
    def _check_exit_conditions(self, position: TradingPosition) -> Optional[str]:
        """Check if position should be exited"""
        current_price = position.current_price
        
        if position.signal_type == "BUY":
            # Stop loss hit
            if current_price <= position.stop_loss:
                return "stop_loss"
            # Take profit hit
            if current_price >= position.take_profit:
                return "take_profit"
            # Trailing stop hit
            if position.trailing_stop and current_price <= position.trailing_stop:
                return "trailing_stop"
        else:  # SELL
            # Stop loss hit
            if current_price >= position.stop_loss:
                return "stop_loss"
            # Take profit hit
            if current_price <= position.take_profit:
                return "take_profit"
            # Trailing stop hit
            if position.trailing_stop and current_price >= position.trailing_stop:
                return "trailing_stop"
        
        # Time-based exit (optional)
        time_elapsed = datetime.now() - position.entry_time
        if time_elapsed > timedelta(hours=24):  # Close after 24 hours
            return "time_limit"
        
        return None
    
    def _handle_position_exit(self, position: TradingPosition, exit_reason: str) -> List[str]:
        """Handle position exit and generate alerts"""
        alerts = []
        
        position.exit_time = datetime.now()
        position.status = PositionStatus(exit_reason)
        
        # Calculate final P&L
        final_pnl = position.profit_loss
        final_pct = position.profit_pct
        
        # Generate exit alert
        if exit_reason == "take_profit":
            alert = f"🎯 PROFIT TARGET HIT! {position.symbol} +${final_pnl:.2f} (+{final_pct:.1f}%)"
            alerts.append(alert)
        elif exit_reason == "stop_loss":
            alert = f"⛔ STOP LOSS HIT: {position.symbol} -${abs(final_pnl):.2f} ({final_pct:.1f}%)"
            alerts.append(alert)
        elif exit_reason == "trailing_stop":
            alert = f"📈 TRAILING STOP: {position.symbol} +${final_pnl:.2f} (+{final_pct:.1f}%)"
            alerts.append(alert)
        else:
            alert = f"⏰ TIME EXIT: {position.symbol} {'+' if final_pnl > 0 else ''}${final_pnl:.2f}"
            alerts.append(alert)
        
        # Move to history
        self.position_history.append(position)
        del self.active_positions[position.symbol]
        
        return alerts
    
    def _update_trailing_stop(self, position: TradingPosition) -> List[str]:
        """Update trailing stop loss"""
        alerts = []
        current_price = position.current_price
        
        if position.signal_type == "BUY":
            # Calculate new trailing stop (e.g., 3% below current high)
            trailing_distance = current_price * 0.03
            new_trailing_stop = current_price - trailing_distance
            
            # Only update if new stop is higher than current
            if not position.trailing_stop or new_trailing_stop > position.trailing_stop:
                old_stop = position.trailing_stop or position.stop_loss
                position.trailing_stop = new_trailing_stop
                
                alerts.append(f"📊 {position.symbol} trailing stop updated: ${new_trailing_stop:.4f}")
        
        return alerts
    
    def _check_milestones(self, position: TradingPosition) -> List[str]:
        """Check for profit/loss milestones"""
        alerts = []
        profit_pct = position.profit_pct
        
        # Check for milestone alerts (5%, 10%, 15%, etc.)
        milestones = [5, 10, 15, 20, 25, 30]
        
        for milestone in milestones:
            alert_key = f"milestone_{milestone}"
            if alert_key not in position.alerts_sent:
                if profit_pct >= milestone:
                    alerts.append(f"🚀 {position.symbol} up {milestone}%! Current: +{profit_pct:.1f}%")
                    position.alerts_sent.append(alert_key)
                elif profit_pct <= -milestone:
                    alerts.append(f"⚠️ {position.symbol} down {milestone}%. Current: {profit_pct:.1f}%")
                    position.alerts_sent.append(alert_key)
        
        return alerts
    
    def _send_alert(self, message: str):
        """Send alert to user (push notification, sound, etc.)"""
        print(f"🔔 ALERT: {message}")
        # In real app: send push notification, play sound, etc.
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        total_value = 0
        total_pnl = 0
        winning_positions = 0
        losing_positions = 0
        
        # Active positions
        for position in self.active_positions.values():
            total_value += position.position_size
            total_pnl += position.profit_loss
            if position.profit_loss > 0:
                winning_positions += 1
            elif position.profit_loss < 0:
                losing_positions += 1
        
        # Historical positions (last 30 days)
        recent_history = [
            p for p in self.position_history 
            if p.exit_time and (datetime.now() - p.exit_time).days <= 30
        ]
        
        historical_pnl = sum(p.profit_loss for p in recent_history)
        win_rate = 0
        if recent_history:
            wins = sum(1 for p in recent_history if p.profit_loss > 0)
            win_rate = (wins / len(recent_history)) * 100
        
        return {
            'active_positions': len(self.active_positions),
            'suggested_positions': len(self.suggested_positions),
            'total_portfolio_value': total_value,
            'unrealized_pnl': total_pnl,
            'realized_pnl_30d': historical_pnl,
            'total_pnl_30d': total_pnl + historical_pnl,
            'win_rate_30d': win_rate,
            'winning_positions': winning_positions,
            'losing_positions': losing_positions
        }
    
    def get_position_suggestions(self) -> List[TradingPosition]:
        """Get current position suggestions"""
        return list(self.suggested_positions.values())
    
    def get_active_positions(self) -> List[TradingPosition]:
        """Get active positions being monitored"""
        return list(self.active_positions.values())

# Example usage and testing
if __name__ == "__main__":
    print("🎯 MOBILE TRADING - BUY/SELL RECOMMENDATION SYSTEM")
    print("=" * 60)
    
    # Initialize position manager
    pm = PositionManager()
    
    # Simulate a buy signal
    signal_data = {
        'symbol': 'BTC/USDT',
        'signal_type': 'BUY',
        'price': 45000.0,
        'strength': 85,
        'timestamp': datetime.now()
    }
    
    # Create suggestion
    suggestion = pm.suggest_position('BTC/USDT', signal_data)
    
    print(f"📊 NEW SUGGESTION:")
    print(f"   Symbol: {suggestion.symbol}")
    print(f"   Type: {suggestion.signal_type}")
    print(f"   Entry: ${suggestion.entry_price:,.2f}")
    print(f"   Stop Loss: ${suggestion.stop_loss:,.2f}")
    print(f"   Take Profit: ${suggestion.take_profit:,.2f}")
    print(f"   Position Size: ${suggestion.position_size:,.2f}")
    print(f"   Risk/Reward: {suggestion.risk_reward_ratio:.1f}:1")
    print(f"   Confidence: {suggestion.confidence}%")
    
    # User accepts suggestion
    print(f"\n✅ User accepts BTC/USDT position")
    pm.accept_suggestion('BTC/USDT')
    
    # Simulate price updates
    print(f"\n📈 MONITORING POSITION:")
    
    price_updates = [45500, 46000, 46500, 47000, 46800, 47500]
    
    for price in price_updates:
        result = pm.update_position('BTC/USDT', price)
        position = result['position']
        
        if position:
            print(f"   Price: ${price:,.2f} | P&L: ${position.profit_loss:,.2f} ({position.profit_pct:+.1f}%)")
            
            for alert in result['alerts']:
                print(f"   🔔 {alert}")
    
    # Portfolio summary
    print(f"\n📊 PORTFOLIO SUMMARY:")
    summary = pm.get_portfolio_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")
