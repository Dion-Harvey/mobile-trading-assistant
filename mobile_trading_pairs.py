# Mobile Trading App - Extended Trading Pairs Configuration

# TIER 1: Major Cryptocurrencies (Always monitored)
TIER_1_PAIRS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT',
    'SOL/USDT', 'DOT/USDT', 'AVAX/USDT', 'MATIC/USDT', 'LINK/USDT'
]

# TIER 2: Popular Altcoins (High liquidity)
TIER_2_PAIRS = [
    'UNI/USDT', 'LTC/USDT', 'ALGO/USDT', 'ATOM/USDT', 'VET/USDT',
    'FIL/USDT', 'TRX/USDT', 'ETC/USDT', 'XLM/USDT', 'BCH/USDT',
    'ICP/USDT', 'NEAR/USDT', 'HBAR/USDT', 'MANA/USDT', 'SAND/USDT'
]

# TIER 3: Emerging & DeFi Tokens (Volatile opportunities)
TIER_3_PAIRS = [
    'CRO/USDT', 'APE/USDT', 'LDO/USDT', 'SHIB/USDT', 'DOGE/USDT',
    'FTM/USDT', 'THETA/USDT', 'AAVE/USDT', 'COMP/USDT', 'MKR/USDT',
    'SUSHI/USDT', 'YFI/USDT', 'ZEC/USDT', 'DASH/USDT', 'EOS/USDT'
]

# TIER 4: Specialty & Gaming Tokens (High volatility)
TIER_4_PAIRS = [
    'AXS/USDT', 'ENJ/USDT', 'GALA/USDT', 'CHZ/USDT', 'BAT/USDT',
    'ZIL/USDT', 'ONE/USDT', 'CELO/USDT', 'ANKR/USDT', 'SKL/USDT'
]

# MOBILE APP CONFIGURATION
class MobileTradingPairs:
    def __init__(self):
        self.all_pairs = TIER_1_PAIRS + TIER_2_PAIRS + TIER_3_PAIRS + TIER_4_PAIRS
        self.total_pairs = len(self.all_pairs)
        
    def get_pairs_by_tier(self, tier_level: str = "all"):
        """Get trading pairs by tier for mobile display"""
        if tier_level == "tier1":
            return TIER_1_PAIRS
        elif tier_level == "tier2":
            return TIER_1_PAIRS + TIER_2_PAIRS
        elif tier_level == "tier3":
            return TIER_1_PAIRS + TIER_2_PAIRS + TIER_3_PAIRS
        else:
            return self.all_pairs
    
    def get_mobile_config(self):
        """Mobile-optimized configuration"""
        return {
            'total_pairs': self.total_pairs,
            'default_view': TIER_1_PAIRS,  # Show top 10 by default
            'expandable_tiers': {
                'Major Cryptos (10)': TIER_1_PAIRS,
                'Popular Alts (15)': TIER_2_PAIRS,
                'DeFi & Emerging (15)': TIER_3_PAIRS,
                'Gaming & Specialty (10)': TIER_4_PAIRS
            },
            'quick_favorites': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT'],
            'scan_interval': 10,  # seconds between scans
            'max_concurrent': 5   # pairs analyzed simultaneously
        }

# MOBILE UI SECTIONS
MOBILE_SECTIONS = {
    'watchlist': TIER_1_PAIRS[:6],      # Top 6 on main screen
    'trending': [],                      # Dynamic based on volume
    'favorites': [],                     # User-selected
    'all_markets': 'TIER_1_PAIRS + TIER_2_PAIRS + TIER_3_PAIRS + TIER_4_PAIRS'
}

# PERFORMANCE OPTIMIZATIONS FOR MOBILE
MOBILE_OPTIMIZATIONS = {
    'lazy_loading': True,                # Load pairs as user scrolls
    'background_monitoring': TIER_1_PAIRS,  # Only monitor favorites in background
    'signal_priority': {
        'critical': TIER_1_PAIRS,        # Always show signals
        'high': TIER_1_PAIRS + TIER_2_PAIRS,  # Show if above 70% strength
        'medium': 'all_pairs'            # Show if above 80% strength
    },
    'data_compression': True,            # Compress historical data
    'cache_duration': 30                 # seconds
}

if __name__ == "__main__":
    mobile_config = MobileTradingPairs()
    print(f"📱 MOBILE TRADING APP CONFIGURATION")
    print(f"🎯 Total Trading Pairs: {mobile_config.total_pairs}")
    print(f"⭐ Default View: {len(TIER_1_PAIRS)} major pairs")
    print(f"🔍 Full Coverage: {len(mobile_config.all_pairs)} pairs")
    print(f"💡 Smart tiered loading for optimal performance")
