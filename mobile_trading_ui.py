# Mobile Trading App - UI Layout for Multiple Trading Pairs

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.tabs import TabPanel, TabbedPanel
from kivy.uix.popup import Popup
from kivy.clock import Clock
from mobile_trading_pairs import MobileTradingPairs, TIER_1_PAIRS, TIER_2_PAIRS
from position_manager import PositionManager, PositionStatus

class TradingPairCard(BoxLayout):
    """Individual trading pair display card"""
    def __init__(self, symbol, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height='60dp', **kwargs)
        self.symbol = symbol
        
        # Symbol name
        self.symbol_label = Label(
            text=symbol,
            size_hint_x=0.25,
            font_size='14sp',
            bold=True
        )
        
        # Price
        self.price_label = Label(
            text="$0.00",
            size_hint_x=0.2,
            font_size='12sp'
        )
        
        # Change %
        self.change_label = Label(
            text="0.00%",
            size_hint_x=0.15,
            font_size='12sp'
        )
        
        # Signal strength
        self.signal_label = Label(
            text="--",
            size_hint_x=0.1,
            font_size='10sp'
        )
        
        # Position status (NEW!)
        self.position_label = Label(
            text="--",
            size_hint_x=0.15,
            font_size='10sp'
        )
        
        # Buy/Alert button (ENHANCED!)
        self.action_btn = Button(
            text="�",
            size_hint_x=0.15,
            font_size='12sp',
            on_release=self.show_position_options
        )
        
        self.add_widget(self.symbol_label)
        self.add_widget(self.price_label)
        self.add_widget(self.change_label)
        self.add_widget(self.signal_label)
        self.add_widget(self.position_label)
        self.add_widget(self.action_btn)
        
        # Store current market data
        self.current_price = 0.0
        self.signal_strength = 0
    
    def update_data(self, price, change_pct, signal_strength, position_status=""):
        """Update the card with new market data and position status"""
        self.current_price = price
        self.signal_strength = signal_strength
        self.price_label.text = f"${price:.4f}"
        
        # Color code the change
        if change_pct > 0:
            self.change_label.text = f"+{change_pct:.2f}%"
            self.change_label.color = (0, 1, 0, 1)  # Green
        else:
            self.change_label.text = f"{change_pct:.2f}%"
            self.change_label.color = (1, 0, 0, 1)  # Red
        
        # Signal strength with buy/sell recommendations
        if signal_strength > 75:
            self.signal_label.text = f"🚨BUY"
            self.signal_label.color = (0, 1, 0, 1)  # Green for strong buy
            self.action_btn.text = "💰BUY"
            self.action_btn.background_color = (0, 0.8, 0, 1)  # Green button
        elif signal_strength > 60:
            self.signal_label.text = f"�{signal_strength:.0f}"
            self.signal_label.color = (1, 0.7, 0, 1)  # Orange
            self.action_btn.text = "⚡"
            self.action_btn.background_color = (1, 0.7, 0, 1)  # Orange button
        elif signal_strength < -75:
            self.signal_label.text = f"🔻SELL"
            self.signal_label.color = (1, 0, 0, 1)  # Red for strong sell
            self.action_btn.text = "📉SELL"
            self.action_btn.background_color = (1, 0, 0, 1)  # Red button
        else:
            self.signal_label.text = "--"
            self.signal_label.color = (0.5, 0.5, 0.5, 1)  # Gray
            self.action_btn.text = "📊"
            self.action_btn.background_color = (0.3, 0.3, 0.3, 1)  # Gray button
        
        # Position status
        if position_status:
            if "PROFIT" in position_status.upper():
                self.position_label.text = position_status
                self.position_label.color = (0, 1, 0, 1)  # Green for profit
            elif "LOSS" in position_status.upper():
                self.position_label.text = position_status
                self.position_label.color = (1, 0, 0, 1)  # Red for loss
            else:
                self.position_label.text = position_status
                self.position_label.color = (1, 1, 1, 1)  # White for neutral
        else:
            self.position_label.text = "--"
            self.position_label.color = (0.5, 0.5, 0.5, 1)
    
    def show_position_options(self, instance):
        """Show popup with position management options"""
        # Get position manager from parent app
        app = App.get_running_app()
        if hasattr(app, 'position_manager'):
            pm = app.position_manager
            
            # Check if there's a suggestion or active position
            if self.symbol in pm.suggested_positions:
                self.show_suggestion_popup(pm.suggested_positions[self.symbol])
            elif self.symbol in pm.active_positions:
                self.show_active_position_popup(pm.active_positions[self.symbol])
            elif self.signal_strength > 60:  # Strong signal
                self.create_position_suggestion()
            else:
                self.show_market_analysis()
    
    def show_suggestion_popup(self, position):
        """Show popup for position suggestion"""
        content = BoxLayout(orientation='vertical', spacing=10)
        
        # Position details
        content.add_widget(Label(text=f"🎯 {position.symbol} {position.signal_type} SUGGESTION", 
                                font_size='16sp', bold=True))
        content.add_widget(Label(text=f"Entry Price: ${position.entry_price:.4f}"))
        content.add_widget(Label(text=f"Stop Loss: ${position.stop_loss:.4f}"))
        content.add_widget(Label(text=f"Take Profit: ${position.take_profit:.4f}"))
        content.add_widget(Label(text=f"Position Size: ${position.position_size:.2f}"))
        content.add_widget(Label(text=f"Risk/Reward: {position.risk_reward_ratio:.1f}:1"))
        content.add_widget(Label(text=f"Confidence: {position.confidence}%"))
        
        # Action buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        
        accept_btn = Button(text="✅ ACCEPT TRADE", background_color=(0, 0.8, 0, 1))
        decline_btn = Button(text="❌ DECLINE", background_color=(0.8, 0, 0, 1))
        
        def accept_trade(instance):
            app = App.get_running_app()
            app.position_manager.accept_suggestion(self.symbol)
            popup.dismiss()
        
        def decline_trade(instance):
            popup.dismiss()
        
        accept_btn.bind(on_release=accept_trade)
        decline_btn.bind(on_release=decline_trade)
        
        button_layout.add_widget(accept_btn)
        button_layout.add_widget(decline_btn)
        content.add_widget(button_layout)
        
        popup = Popup(title=f"Trade Suggestion: {self.symbol}",
                     content=content,
                     size_hint=(0.9, 0.8))
        popup.open()
    
    def show_active_position_popup(self, position):
        """Show popup for active position management"""
        content = BoxLayout(orientation='vertical', spacing=10)
        
        # Position status
        content.add_widget(Label(text=f"🔄 ACTIVE: {position.symbol} {position.signal_type}", 
                                font_size='16sp', bold=True))
        content.add_widget(Label(text=f"Entry: ${position.entry_price:.4f}"))
        content.add_widget(Label(text=f"Current: ${position.current_price:.4f}"))
        content.add_widget(Label(text=f"P&L: ${position.profit_loss:.2f} ({position.profit_pct:+.1f}%)"))
        content.add_widget(Label(text=f"Stop Loss: ${position.stop_loss:.4f}"))
        content.add_widget(Label(text=f"Take Profit: ${position.take_profit:.4f}"))
        
        if position.trailing_stop:
            content.add_widget(Label(text=f"Trailing Stop: ${position.trailing_stop:.4f}"))
        
        # Action buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        
        close_btn = Button(text="🚪 CLOSE POSITION", background_color=(0.8, 0.4, 0, 1))
        modify_btn = Button(text="⚙️ MODIFY", background_color=(0, 0.4, 0.8, 1))
        
        def close_position(instance):
            # Manual exit
            app = App.get_running_app()
            app.position_manager._handle_position_exit(position, "manual_exit")
            popup.dismiss()
        
        def modify_position(instance):
            popup.dismiss()
            # TODO: Add modify position popup
        
        close_btn.bind(on_release=close_position)
        modify_btn.bind(on_release=modify_position)
        
        button_layout.add_widget(close_btn)
        button_layout.add_widget(modify_btn)
        content.add_widget(button_layout)
        
        popup = Popup(title=f"Position: {self.symbol}",
                     content=content,
                     size_hint=(0.9, 0.8))
        popup.open()
    
    def create_position_suggestion(self):
        """Create a new position suggestion from current signal"""
        signal_data = {
            'symbol': self.symbol,
            'signal_type': 'BUY' if self.signal_strength > 0 else 'SELL',
            'price': self.current_price,
            'strength': abs(self.signal_strength),
            'timestamp': Clock.get_time()
        }
        
        app = App.get_running_app()
        if hasattr(app, 'position_manager'):
            suggestion = app.position_manager.suggest_position(self.symbol, signal_data)
            self.show_suggestion_popup(suggestion)
    
    def show_market_analysis(self):
        """Show basic market analysis popup"""
        content = BoxLayout(orientation='vertical', spacing=10)
        
        content.add_widget(Label(text=f"📊 {self.symbol} Analysis", font_size='16sp', bold=True))
        content.add_widget(Label(text=f"Current Price: ${self.current_price:.4f}"))
        content.add_widget(Label(text=f"Signal Strength: {self.signal_strength}"))
        content.add_widget(Label(text="No strong trading signals detected."))
        content.add_widget(Label(text="Monitor for signal strength > 60 for trade opportunities."))
        
        close_btn = Button(text="Close", size_hint_y=0.3)
        content.add_widget(close_btn)
        
        popup = Popup(title=f"Market Analysis: {self.symbol}",
                     content=content,
                     size_hint=(0.8, 0.6))
        
        close_btn.bind(on_release=popup.dismiss)
        popup.open()
    
    def toggle_alert(self, instance):
        """Toggle alert for this pair (legacy method)"""
        # Add to favorites or alert list
        pass

class MarketOverviewScreen(Screen):
    """Main screen showing trading pairs"""
    def __init__(self, **kwargs):
        super().__init__(name='market_overview', **kwargs)
        
        main_layout = BoxLayout(orientation='vertical')
        
        # Tabbed interface for different tiers
        self.tabs = TabbedPanel(do_default_tab=False)
        
        # Create tabs for each tier
        self.create_tier_tabs()
        
        main_layout.add_widget(self.tabs)
        self.add_widget(main_layout)
        
        # Start real-time updates
        Clock.schedule_interval(self.update_market_data, 10)  # Every 10 seconds
    
    def create_tier_tabs(self):
        """Create tabs for different trading pair tiers"""
        mobile_config = MobileTradingPairs()
        
        # Favorites Tab (User's selected pairs)
        favorites_tab = TabPanel(text='⭐ Favorites')
        favorites_layout = self.create_pairs_layout(TIER_1_PAIRS[:6])
        favorites_tab.add_widget(favorites_layout)
        self.tabs.add_widget(favorites_tab)
        
        # Major Cryptos Tab
        major_tab = TabPanel(text='🚀 Major')
        major_layout = self.create_pairs_layout(TIER_1_PAIRS)
        major_tab.add_widget(major_layout)
        self.tabs.add_widget(major_tab)
        
        # All Altcoins Tab
        alt_tab = TabPanel(text='📈 Alts')
        alt_layout = self.create_pairs_layout(TIER_2_PAIRS)
        alt_tab.add_widget(alt_layout)
        self.tabs.add_widget(alt_tab)
        
        # DeFi Tab
        defi_tab = TabPanel(text='🔥 DeFi')
        defi_layout = self.create_pairs_layout(mobile_config.get_pairs_by_tier("tier3")[20:35])
        defi_tab.add_widget(defi_layout)
        self.tabs.add_widget(defi_tab)
        
        # Trending Tab (Dynamic)
        trending_tab = TabPanel(text='📊 Trending')
        trending_layout = self.create_pairs_layout([])  # Will be populated dynamically
        trending_tab.add_widget(trending_layout)
        self.tabs.add_widget(trending_tab)
    
    def create_pairs_layout(self, pairs_list):
        """Create scrollable layout for trading pairs"""
        scroll = ScrollView()
        grid = GridLayout(cols=1, size_hint_y=None, spacing=2)
        grid.bind(minimum_height=grid.setter('height'))
        
        # Add header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp')
        header.add_widget(Label(text='Symbol', size_hint_x=0.25, bold=True))
        header.add_widget(Label(text='Price', size_hint_x=0.2, bold=True))
        header.add_widget(Label(text='Change', size_hint_x=0.15, bold=True))
        header.add_widget(Label(text='Signal', size_hint_x=0.1, bold=True))
        header.add_widget(Label(text='Position', size_hint_x=0.15, bold=True))
        header.add_widget(Label(text='Action', size_hint_x=0.15, bold=True))
        grid.add_widget(header)
        
        # Add trading pair cards
        self.pair_cards = {}
        for symbol in pairs_list:
            card = TradingPairCard(symbol)
            grid.add_widget(card)
            self.pair_cards[symbol] = card
        
        scroll.add_widget(grid)
        return scroll
    
    def update_market_data(self, dt):
        """Update market data for all visible pairs"""
        import random
        
        # Get position manager
        app = App.get_running_app()
        pm = getattr(app, 'position_manager', None)
        
        for symbol, card in self.pair_cards.items():
            # Simulate market data (replace with real data)
            price = random.uniform(0.1, 50000)
            change_pct = random.uniform(-10, 10)
            signal_strength = random.uniform(-100, 100)
            
            # Check position status
            position_status = ""
            if pm:
                # Update any active positions
                if symbol in pm.active_positions:
                    result = pm.update_position(symbol, price)
                    position = result['position']
                    if position:
                        position_status = f"{position.profit_pct:+.1f}%"
                    
                    # Show any alerts
                    for alert in result['alerts']:
                        print(f"🔔 {alert}")
                
                # Check for new suggestions
                elif abs(signal_strength) > 75 and symbol not in pm.suggested_positions:
                    signal_data = {
                        'symbol': symbol,
                        'signal_type': 'BUY' if signal_strength > 0 else 'SELL',
                        'price': price,
                        'strength': abs(signal_strength),
                        'timestamp': Clock.get_time()
                    }
                    
                    # Create suggestion for strong signals
                    suggestion = pm.suggest_position(symbol, signal_data)
                    position_status = f"💡{suggestion.signal_type}"
            
            card.update_data(price, change_pct, signal_strength, position_status)

class SignalAlertsScreen(Screen):
    """Screen for managing signal alerts"""
    def __init__(self, **kwargs):
        super().__init__(name='alerts', **kwargs)
        
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(text='🚨 Signal Alerts', font_size='20sp', size_hint_y=0.1))
        
        # Recent alerts list
        scroll = ScrollView()
        alerts_grid = GridLayout(cols=1, size_hint_y=None)
        alerts_grid.bind(minimum_height=alerts_grid.setter('height'))
        
        # Sample alerts (replace with real alert system)
        alerts = [
            {'symbol': 'BTC/USDT', 'type': 'BUY', 'strength': 85, 'time': '10:30'},
            {'symbol': 'ETH/USDT', 'type': 'SELL', 'strength': 78, 'time': '10:25'},
            {'symbol': 'SOL/USDT', 'type': 'BUY', 'strength': 92, 'time': '10:20'},
        ]
        
        for alert in alerts:
            alert_card = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp')
            alert_card.add_widget(Label(text=alert['symbol'], size_hint_x=0.3))
            alert_card.add_widget(Label(text=alert['type'], size_hint_x=0.2))
            alert_card.add_widget(Label(text=f"{alert['strength']}%", size_hint_x=0.2))
            alert_card.add_widget(Label(text=alert['time'], size_hint_x=0.3))
            alerts_grid.add_widget(alert_card)
        
        scroll.add_widget(alerts_grid)
        layout.add_widget(scroll)
        self.add_widget(layout)

class PositionsScreen(Screen):
    """Screen for managing active positions and suggestions"""
    def __init__(self, **kwargs):
        super().__init__(name='positions', **kwargs)
        
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(text='💼 My Positions', font_size='20sp', size_hint_y=0.1))
        
        # Tabbed interface for different position types
        self.tabs = TabbedPanel(do_default_tab=False)
        
        # Suggestions tab
        suggestions_tab = TabPanel(text='💡 Suggestions')
        self.suggestions_layout = self.create_suggestions_layout()
        suggestions_tab.add_widget(self.suggestions_layout)
        self.tabs.add_widget(suggestions_tab)
        
        # Active positions tab
        active_tab = TabPanel(text='🔄 Active')
        self.active_layout = self.create_active_positions_layout()
        active_tab.add_widget(self.active_layout)
        self.tabs.add_widget(active_tab)
        
        # History tab
        history_tab = TabPanel(text='📊 History')
        self.history_layout = self.create_history_layout()
        history_tab.add_widget(self.history_layout)
        self.tabs.add_widget(history_tab)
        
        layout.add_widget(self.tabs)
        self.add_widget(layout)
        
        # Update every 5 seconds
        Clock.schedule_interval(self.update_positions, 5)
    
    def create_suggestions_layout(self):
        """Create layout for position suggestions"""
        scroll = ScrollView()
        self.suggestions_grid = GridLayout(cols=1, size_hint_y=None, spacing=5)
        self.suggestions_grid.bind(minimum_height=self.suggestions_grid.setter('height'))
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp')
        header.add_widget(Label(text='Symbol', size_hint_x=0.2, bold=True))
        header.add_widget(Label(text='Type', size_hint_x=0.15, bold=True))
        header.add_widget(Label(text='Entry', size_hint_x=0.2, bold=True))
        header.add_widget(Label(text='R:R', size_hint_x=0.15, bold=True))
        header.add_widget(Label(text='Confidence', size_hint_x=0.15, bold=True))
        header.add_widget(Label(text='Action', size_hint_x=0.15, bold=True))
        self.suggestions_grid.add_widget(header)
        
        scroll.add_widget(self.suggestions_grid)
        return scroll
    
    def create_active_positions_layout(self):
        """Create layout for active positions"""
        scroll = ScrollView()
        self.active_grid = GridLayout(cols=1, size_hint_y=None, spacing=5)
        self.active_grid.bind(minimum_height=self.active_grid.setter('height'))
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp')
        header.add_widget(Label(text='Symbol', size_hint_x=0.2, bold=True))
        header.add_widget(Label(text='Type', size_hint_x=0.1, bold=True))
        header.add_widget(Label(text='Entry', size_hint_x=0.15, bold=True))
        header.add_widget(Label(text='Current', size_hint_x=0.15, bold=True))
        header.add_widget(Label(text='P&L', size_hint_x=0.15, bold=True))
        header.add_widget(Label(text='P&L%', size_hint_x=0.1, bold=True))
        header.add_widget(Label(text='Action', size_hint_x=0.15, bold=True))
        self.active_grid.add_widget(header)
        
        scroll.add_widget(self.active_grid)
        return scroll
    
    def create_history_layout(self):
        """Create layout for position history"""
        scroll = ScrollView()
        self.history_grid = GridLayout(cols=1, size_hint_y=None, spacing=5)
        self.history_grid.bind(minimum_height=self.history_grid.setter('height'))
        
        # Portfolio summary
        summary_layout = BoxLayout(orientation='vertical', size_hint_y=None, height='120dp')
        summary_layout.add_widget(Label(text='📊 Portfolio Summary', bold=True))
        
        self.portfolio_labels = {
            'total_pnl': Label(text='Total P&L: $0.00'),
            'win_rate': Label(text='Win Rate: 0%'),
            'active_count': Label(text='Active Positions: 0'),
        }
        
        for label in self.portfolio_labels.values():
            summary_layout.add_widget(label)
        
        self.history_grid.add_widget(summary_layout)
        
        # History header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp')
        header.add_widget(Label(text='Symbol', size_hint_x=0.2, bold=True))
        header.add_widget(Label(text='Type', size_hint_x=0.1, bold=True))
        header.add_widget(Label(text='Exit', size_hint_x=0.2, bold=True))
        header.add_widget(Label(text='P&L', size_hint_x=0.15, bold=True))
        header.add_widget(Label(text='P&L%', size_hint_x=0.15, bold=True))
        header.add_widget(Label(text='Duration', size_hint_x=0.2, bold=True))
        self.history_grid.add_widget(header)
        
        scroll.add_widget(self.history_grid)
        return scroll
    
    def update_positions(self, dt):
        """Update all position displays"""
        app = App.get_running_app()
        pm = getattr(app, 'position_manager', None)
        
        if not pm:
            return
        
        # Clear existing entries (except headers)
        self.clear_grid_content(self.suggestions_grid, 1)  # Keep header
        self.clear_grid_content(self.active_grid, 1)
        self.clear_grid_content(self.history_grid, 2)  # Keep summary + header
        
        # Update suggestions
        for suggestion in pm.get_position_suggestions():
            self.add_suggestion_row(suggestion)
        
        # Update active positions
        for position in pm.get_active_positions():
            self.add_active_position_row(position)
        
        # Update portfolio summary
        summary = pm.get_portfolio_summary()
        self.portfolio_labels['total_pnl'].text = f"Total P&L: ${summary['total_pnl_30d']:.2f}"
        self.portfolio_labels['win_rate'].text = f"Win Rate: {summary['win_rate_30d']:.1f}%"
        self.portfolio_labels['active_count'].text = f"Active Positions: {summary['active_positions']}"
        
        # Update history (last 10 entries)
        for position in pm.position_history[-10:]:
            self.add_history_row(position)
    
    def clear_grid_content(self, grid, keep_count):
        """Clear grid content but keep first 'keep_count' items"""
        children = list(grid.children)
        for i, child in enumerate(children):
            if i < len(children) - keep_count:
                grid.remove_widget(child)
    
    def add_suggestion_row(self, suggestion):
        """Add suggestion row to suggestions grid"""
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp')
        
        row.add_widget(Label(text=suggestion.symbol, size_hint_x=0.2))
        
        # Color-coded signal type
        type_label = Label(text=suggestion.signal_type, size_hint_x=0.15)
        if suggestion.signal_type == "BUY":
            type_label.color = (0, 1, 0, 1)  # Green
        else:
            type_label.color = (1, 0, 0, 1)  # Red
        row.add_widget(type_label)
        
        row.add_widget(Label(text=f"${suggestion.entry_price:.2f}", size_hint_x=0.2))
        row.add_widget(Label(text=f"{suggestion.risk_reward_ratio:.1f}:1", size_hint_x=0.15))
        row.add_widget(Label(text=f"{suggestion.confidence}%", size_hint_x=0.15))
        
        # Accept button
        accept_btn = Button(text="✅", size_hint_x=0.15, background_color=(0, 0.8, 0, 1))
        accept_btn.bind(on_release=lambda x: self.accept_suggestion(suggestion.symbol))
        row.add_widget(accept_btn)
        
        self.suggestions_grid.add_widget(row)
    
    def add_active_position_row(self, position):
        """Add active position row to active grid"""
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp')
        
        row.add_widget(Label(text=position.symbol, size_hint_x=0.2))
        
        # Color-coded signal type
        type_label = Label(text=position.signal_type, size_hint_x=0.1)
        if position.signal_type == "BUY":
            type_label.color = (0, 1, 0, 1)  # Green
        else:
            type_label.color = (1, 0, 0, 1)  # Red
        row.add_widget(type_label)
        
        row.add_widget(Label(text=f"${position.entry_price:.2f}", size_hint_x=0.15))
        row.add_widget(Label(text=f"${position.current_price:.2f}", size_hint_x=0.15))
        
        # Color-coded P&L
        pnl_label = Label(text=f"${position.profit_loss:.2f}", size_hint_x=0.15)
        pnl_pct_label = Label(text=f"{position.profit_pct:+.1f}%", size_hint_x=0.1)
        
        if position.profit_loss > 0:
            pnl_label.color = (0, 1, 0, 1)  # Green
            pnl_pct_label.color = (0, 1, 0, 1)
        else:
            pnl_label.color = (1, 0, 0, 1)  # Red
            pnl_pct_label.color = (1, 0, 0, 1)
        
        row.add_widget(pnl_label)
        row.add_widget(pnl_pct_label)
        
        # Close button
        close_btn = Button(text="🚪", size_hint_x=0.15, background_color=(0.8, 0.4, 0, 1))
        close_btn.bind(on_release=lambda x: self.close_position(position.symbol))
        row.add_widget(close_btn)
        
        self.active_grid.add_widget(row)
    
    def add_history_row(self, position):
        """Add history row to history grid"""
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp')
        
        row.add_widget(Label(text=position.symbol, size_hint_x=0.2))
        
        # Color-coded signal type
        type_label = Label(text=position.signal_type, size_hint_x=0.1)
        if position.signal_type == "BUY":
            type_label.color = (0, 1, 0, 1)
        else:
            type_label.color = (1, 0, 0, 1)
        row.add_widget(type_label)
        
        # Exit reason
        exit_text = position.status.value.replace('_', ' ').title()
        row.add_widget(Label(text=exit_text, size_hint_x=0.2))
        
        # Color-coded P&L
        pnl_label = Label(text=f"${position.profit_loss:.2f}", size_hint_x=0.15)
        pnl_pct_label = Label(text=f"{position.profit_pct:+.1f}%", size_hint_x=0.15)
        
        if position.profit_loss > 0:
            pnl_label.color = (0, 1, 0, 1)
            pnl_pct_label.color = (0, 1, 0, 1)
        else:
            pnl_label.color = (1, 0, 0, 1)
            pnl_pct_label.color = (1, 0, 0, 1)
        
        row.add_widget(pnl_label)
        row.add_widget(pnl_pct_label)
        
        # Duration
        if position.exit_time:
            duration = position.exit_time - position.entry_time
            hours = duration.total_seconds() / 3600
            row.add_widget(Label(text=f"{hours:.1f}h", size_hint_x=0.2))
        else:
            row.add_widget(Label(text="--", size_hint_x=0.2))
        
        self.history_grid.add_widget(row)
    
    def accept_suggestion(self, symbol):
        """Accept a position suggestion"""
        app = App.get_running_app()
        if hasattr(app, 'position_manager'):
            app.position_manager.accept_suggestion(symbol)
    
    def close_position(self, symbol):
        """Close an active position"""
        app = App.get_running_app()
        if hasattr(app, 'position_manager') and symbol in app.position_manager.active_positions:
            position = app.position_manager.active_positions[symbol]
            app.position_manager._handle_position_exit(position, "manual_exit")

class MobileTradingApp(App):
    """Main mobile trading application"""
    def build(self):
        # Initialize position manager
        self.position_manager = PositionManager()
        
        sm = ScreenManager()
        
        # Add screens
        sm.add_widget(MarketOverviewScreen())
        sm.add_widget(SignalAlertsScreen())
        sm.add_widget(PositionsScreen())
        
        return sm

# Performance optimizations for mobile
MOBILE_SETTINGS = {
    'max_pairs_per_tab': 20,           # Limit pairs per tab for performance
    'lazy_loading': True,              # Load data as user scrolls
    'background_updates': 6,           # Only update top 6 pairs in background
    'signal_threshold': 50,            # Only show signals above 50% strength
    'update_interval': 10,             # Update every 10 seconds
    'cache_duration': 30,              # Cache data for 30 seconds
}

if __name__ == '__main__':
    print("📱 MOBILE TRADING APP WITH BUY/SELL RECOMMENDATIONS")
    print("=" * 60)
    print("🎯 Features:")
    print("   ✅ AI-Powered Buy/Sell Suggestions")
    print("   ✅ Automated Position Monitoring")
    print("   ✅ Smart Stop-Loss & Take-Profit")
    print("   ✅ Real-Time Exit Alerts")
    print("   ✅ Risk Management & Position Sizing")
    print("   ✅ Portfolio Performance Tracking")
    print(f"📊 Optimized for performance: {MOBILE_SETTINGS}")
    print("\n🚀 Starting app with 50+ trading pairs and position management...")
    MobileTradingApp().run()
