import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
import ccxt
import talib
import requests
import threading
import time
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
from plyer import notification
import winsound  # For Windows sound alerts

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

@dataclass
class MarketSignal:
    symbol: str
    timeframe: str
    signal_type: str
    strength: float  # 0-100
    direction: str   # bullish/bearish
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    confidence: str  # low/medium/high/critical
    indicators: Dict
    timestamp: datetime

class TechnicalAnalyzer:
    def __init__(self):
        self.indicators = {}
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive technical indicators"""
        if len(df) < 50:
            return {}
        
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values
        
        indicators = {}
        
        try:
            # Price action
            indicators['current_price'] = close[-1]
            indicators['price_change_pct'] = ((close[-1] - close[-2]) / close[-2]) * 100
            
            # RSI
            rsi = talib.RSI(close, timeperiod=14)
            indicators['rsi'] = rsi[-1]
            indicators['rsi_oversold'] = rsi[-1] < 30
            indicators['rsi_overbought'] = rsi[-1] > 70
            indicators['rsi_divergence'] = self._detect_rsi_divergence(close, rsi)
            
            # MACD
            macd_line, macd_signal, macd_histogram = talib.MACD(close)
            indicators['macd_line'] = macd_line[-1]
            indicators['macd_signal'] = macd_signal[-1]
            indicators['macd_histogram'] = macd_histogram[-1]
            indicators['macd_bullish'] = (macd_line[-1] > macd_signal[-1] and 
                                        macd_histogram[-1] > macd_histogram[-2])
            
            # Moving Averages
            ema_9 = talib.EMA(close, timeperiod=9)
            ema_21 = talib.EMA(close, timeperiod=21)
            ema_50 = talib.EMA(close, timeperiod=50)
            indicators['ema_9'] = ema_9[-1]
            indicators['ema_21'] = ema_21[-1]
            indicators['ema_50'] = ema_50[-1]
            indicators['ema_bullish_alignment'] = ema_9[-1] > ema_21[-1] > ema_50[-1]
            indicators['price_above_ema21'] = close[-1] > ema_21[-1]
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20)
            indicators['bb_upper'] = bb_upper[-1]
            indicators['bb_middle'] = bb_middle[-1]
            indicators['bb_lower'] = bb_lower[-1]
            bb_width = (bb_upper[-1] - bb_lower[-1]) / bb_middle[-1]
            indicators['bb_width'] = bb_width
            indicators['bb_squeeze'] = bb_width < 0.1
            indicators['bb_position'] = 'upper' if close[-1] > bb_upper[-1] else 'lower' if close[-1] < bb_lower[-1] else 'middle'
            
            # Enhanced Volume Analysis
            avg_volume_20 = np.mean(volume[-20:])
            avg_volume_50 = np.mean(volume[-50:])
            indicators['current_volume'] = volume[-1]
            indicators['avg_volume'] = avg_volume_20
            indicators['avg_volume_50'] = avg_volume_50
            
            # Multiple volume surge thresholds based on methodology
            indicators['volume_surge'] = volume[-1] > (avg_volume_20 * 2)
            indicators['volume_spike_3x'] = volume[-1] > (avg_volume_20 * 3)  # Strong spike
            indicators['volume_spike_5x'] = volume[-1] > (avg_volume_20 * 5)  # Extreme spike
            indicators['volume_ratio'] = volume[-1] / avg_volume_20
            
            # ENHANCED Phase 1: Advanced Volume Surge Patterns
            # Pattern 1: Sustained volume (3+ consecutive high volume bars)
            sustained_vol_count = sum(1 for i in range(-3, 0) if volume[i] > avg_volume_20 * 1.5)
            indicators['sustained_volume'] = sustained_vol_count >= 3
            
            # Pattern 2: Accelerating volume (each bar higher than previous)
            vol_acceleration = all(volume[i] > volume[i-1] for i in range(-2, 0))
            indicators['volume_acceleration'] = vol_acceleration
            
            # Pattern 3: Volume breakout (highest volume in 20 periods)
            indicators['volume_breakout'] = volume[-1] == max(volume[-20:])
            
            # Pattern 4: Smart money volume (high volume + small price change = accumulation)
            price_change_pct = abs((close[-1] - close[-2]) / close[-2]) * 100
            indicators['smart_money_volume'] = (volume[-1] > avg_volume_20 * 2) and (price_change_pct < 2)
            
            # Pattern 5: Phase 1 multiplier for confirmed volume spikes
            volume_phase1_score = 0
            if indicators['volume_spike_5x']:
                volume_phase1_score = 10  # Maximum boost
            elif indicators['volume_spike_3x']:
                volume_phase1_score = 7
            elif indicators['volume_surge'] and indicators['sustained_volume']:
                volume_phase1_score = 5
            elif indicators['volume_acceleration']:
                volume_phase1_score = 3
            indicators['volume_phase1_score'] = volume_phase1_score
            
            # Volume momentum (last 3 bars vs previous 3 bars)
            recent_vol = np.mean(volume[-3:])
            previous_vol = np.mean(volume[-6:-3])
            indicators['volume_momentum'] = recent_vol / previous_vol if previous_vol > 0 else 1
            
            # Volume trend (increasing/decreasing over last 5 bars)
            volume_trend = np.polyfit(range(5), volume[-5:], 1)[0]
            indicators['volume_trend_increasing'] = volume_trend > 0
            
            # ATR for volatility
            atr = talib.ATR(high, low, close, timeperiod=14)
            indicators['atr'] = atr[-1]
            indicators['atr_pct'] = (atr[-1] / close[-1]) * 100
            
            # Support/Resistance
            recent_high = np.max(high[-20:])
            recent_low = np.min(low[-20:])
            indicators['recent_high'] = recent_high
            indicators['recent_low'] = recent_low
            indicators['near_resistance'] = abs(close[-1] - recent_high) / close[-1] < 0.02
            indicators['near_support'] = abs(close[-1] - recent_low) / close[-1] < 0.02
            
            # Breakout detection
            indicators['breakout_up'] = close[-1] > recent_high and volume[-1] > avg_volume_20 * 1.5
            indicators['breakdown'] = close[-1] < recent_low and volume[-1] > avg_volume_20 * 1.5
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}
    
    def _detect_rsi_divergence(self, close: np.ndarray, rsi: np.ndarray) -> bool:
        """Detect RSI divergence patterns"""
        if len(close) < 20:
            return False
        
        try:
            # Look for bullish divergence in last 20 periods
            recent_close = close[-20:]
            recent_rsi = rsi[-20:]
            
            # Find local lows
            price_lows = []
            rsi_lows = []
            
            for i in range(2, len(recent_close)-2):
                if (recent_close[i] < recent_close[i-1] and recent_close[i] < recent_close[i+1] and
                    recent_close[i] < recent_close[i-2] and recent_close[i] < recent_close[i+2]):
                    price_lows.append((i, recent_close[i]))
                    rsi_lows.append((i, recent_rsi[i]))
            
            if len(price_lows) >= 2:
                # Check for bullish divergence (price lower low, RSI higher low)
                last_price_low = price_lows[-1][1]
                prev_price_low = price_lows[-2][1]
                last_rsi_low = rsi_lows[-1][1]
                prev_rsi_low = rsi_lows[-2][1]
                
                if last_price_low < prev_price_low and last_rsi_low > prev_rsi_low:
                    return True
            
            return False
        except:
            return False

class OnChainDataManager:
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutes for on-chain data
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TradingBot/1.0'
        })
    
    def get_exchange_flows(self, symbol: str) -> Dict:
        """Get exchange inflows/outflows using free APIs"""
        try:
            cache_key = f"exchange_flows_{symbol}"
            current_time = time.time()
            
            # Check cache
            if (cache_key in self.cache and 
                current_time - self.cache[cache_key]['timestamp'] < self.cache_duration):
                return self.cache[cache_key]['data']
            
            # Use CoinGecko for basic market data that can indicate flows
            flows_data = self._get_coingecko_market_data(symbol)
            
            # Estimate flows based on volume and price action patterns
            estimated_flows = self._estimate_flows_from_market_data(flows_data)
            
            # Cache the data
            self.cache[cache_key] = {
                'data': estimated_flows,
                'timestamp': current_time
            }
            
            return estimated_flows
            
        except Exception as e:
            logger.error(f"Error fetching exchange flows for {symbol}: {e}")
            return {
                'net_flow': 0,
                'inflow_24h': 0,
                'outflow_24h': 0,
                'whale_activity': False,
                'smart_money_flow': 0
            }
    
    def get_stablecoin_flows(self) -> Dict:
        """Get stablecoin market data using free APIs"""
        try:
            cache_key = "stablecoin_flows"
            current_time = time.time()
            
            # Check cache
            if (cache_key in self.cache and 
                current_time - self.cache[cache_key]['timestamp'] < self.cache_duration):
                return self.cache[cache_key]['data']
            
            # Get USDT and USDC market data from CoinGecko
            stablecoin_data = self._get_stablecoin_market_data()
            
            # Cache the data
            self.cache[cache_key] = {
                'data': stablecoin_data,
                'timestamp': current_time
            }
            
            return stablecoin_data
            
        except Exception as e:
            logger.error(f"Error fetching stablecoin flows: {e}")
            return {
                'total_inflow_24h': 0,
                'usdt_inflow': 0,
                'usdc_inflow': 0,
                'flow_velocity': 0
            }
    
    def _get_coingecko_market_data(self, symbol: str) -> Dict:
        """Get market data from CoinGecko free API"""
        try:
            # Convert symbol format (BTC/USDT -> bitcoin)
            coin_id = self._symbol_to_coingecko_id(symbol)
            if not coin_id:
                return {}
            
            # Get market data
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': '1',  # Last 24 hours
                'interval': 'hourly'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'prices': data.get('prices', []),
                'volumes': data.get('total_volumes', []),
                'market_caps': data.get('market_caps', [])
            }
            
        except Exception as e:
            logger.error(f"Error fetching CoinGecko data: {e}")
            return {}
    
    def _get_stablecoin_market_data(self) -> Dict:
        """Get stablecoin market data from CoinGecko"""
        try:
            stablecoins = ['tether', 'usd-coin', 'binance-usd']  # USDT, USDC, BUSD
            total_volume_change = 0
            individual_data = {}
            
            for coin in stablecoins:
                url = f"https://api.coingecko.com/api/v3/coins/{coin}"
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                market_data = data.get('market_data', {})
                volume_24h = market_data.get('total_volume', {}).get('usd', 0)
                volume_change = market_data.get('total_volume_change_24h', 0)
                
                individual_data[coin] = {
                    'volume_24h': volume_24h,
                    'volume_change': volume_change
                }
                
                total_volume_change += volume_change
            
            return {
                'total_inflow_24h': max(0, total_volume_change),  # Positive changes only
                'usdt_inflow': individual_data.get('tether', {}).get('volume_change', 0),
                'usdc_inflow': individual_data.get('usd-coin', {}).get('volume_change', 0),
                'flow_velocity': total_volume_change / len(stablecoins) if stablecoins else 0
            }
            
        except Exception as e:
            logger.error(f"Error fetching stablecoin data: {e}")
            return {
                'total_inflow_24h': 0,
                'usdt_inflow': 0,
                'usdc_inflow': 0,
                'flow_velocity': 0
            }
    
    def _estimate_flows_from_market_data(self, market_data: Dict) -> Dict:
        """Estimate exchange flows from market data patterns"""
        try:
            volumes = market_data.get('volumes', [])
            prices = market_data.get('prices', [])
            
            if len(volumes) < 2 or len(prices) < 2:
                return {
                    'net_flow': 0,
                    'inflow_24h': 0,
                    'outflow_24h': 0,
                    'whale_activity': False,
                    'smart_money_flow': 0
                }
            
            # Calculate volume trend
            recent_volumes = [v[1] for v in volumes[-6:]]  # Last 6 hours
            earlier_volumes = [v[1] for v in volumes[-12:-6]]  # Previous 6 hours
            
            recent_avg = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
            earlier_avg = sum(earlier_volumes) / len(earlier_volumes) if earlier_volumes else 0
            
            volume_change = recent_avg - earlier_avg
            
            # Calculate price trend
            recent_prices = [p[1] for p in prices[-6:]]
            price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100 if recent_prices else 0
            
            # Estimate flows based on volume and price patterns
            # High volume + price up = potential outflows (accumulation)
            # High volume + price down = potential inflows (selling)
            
            if volume_change > 0:
                if price_change > 0:
                    # Volume up, price up = likely accumulation (outflows from exchanges)
                    net_flow = -volume_change * 0.3  # Negative = outflows
                    smart_money_flow = volume_change * 0.2
                else:
                    # Volume up, price down = likely selling (inflows to exchanges)
                    net_flow = volume_change * 0.3  # Positive = inflows
                    smart_money_flow = -volume_change * 0.1
            else:
                net_flow = 0
                smart_money_flow = 0
            
            # Whale activity detection (very high volume spikes)
            max_volume = max(recent_volumes) if recent_volumes else 0
            avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
            whale_activity = max_volume > avg_volume * 3 if avg_volume > 0 else False
            
            return {
                'net_flow': net_flow,
                'inflow_24h': max(0, net_flow),
                'outflow_24h': max(0, -net_flow),
                'whale_activity': whale_activity,
                'smart_money_flow': smart_money_flow
            }
            
        except Exception as e:
            logger.error(f"Error estimating flows: {e}")
            return {
                'net_flow': 0,
                'inflow_24h': 0,
                'outflow_24h': 0,
                'whale_activity': False,
                'smart_money_flow': 0
            }
    
    def _symbol_to_coingecko_id(self, symbol: str) -> str:
        """Convert trading symbol to CoinGecko ID"""
        # Remove /USDT, /USD, etc. and get base currency
        base_symbol = symbol.split('/')[0].upper()
        
        # Common mappings
        symbol_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'ADA': 'cardano',
            'SOL': 'solana',
            'XRP': 'ripple',
            'DOT': 'polkadot',
            'AVAX': 'avalanche-2',
            'MATIC': 'matic-network',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'LTC': 'litecoin',
            'BCH': 'bitcoin-cash',
            'ALGO': 'algorand',
            'VET': 'vechain',
            'FIL': 'filecoin',
            'TRX': 'tron',
            'ETC': 'ethereum-classic',
            'XLM': 'stellar',
            'ATOM': 'cosmos',
            'HBAR': 'hedera-hashgraph',
            'NEAR': 'near',
            'MANA': 'decentraland',
            'SAND': 'the-sandbox',
            'CRO': 'crypto-com-chain',
            'APE': 'apecoin',
            'LDO': 'lido-dao',
            'SHIB': 'shiba-inu'
        }
        
        return symbol_map.get(base_symbol, '')
    
    def get_network_activity(self, symbol: str) -> Dict:
        """Get basic network activity using free APIs"""
        try:
            cache_key = f"network_activity_{symbol}"
            current_time = time.time()
            
            # Check cache
            if (cache_key in self.cache and 
                current_time - self.cache[cache_key]['timestamp'] < self.cache_duration):
                return self.cache[cache_key]['data']
            
            coin_id = self._symbol_to_coingecko_id(symbol)
            if not coin_id:
                return {}
            
            # Get basic coin data from CoinGecko
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'true',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            market_data = data.get('market_data', {})
            community_data = data.get('community_data', {})
            
            activity_data = {
                'market_cap_change_24h': market_data.get('market_cap_change_percentage_24h', 0),
                'price_change_24h': market_data.get('price_change_percentage_24h', 0),
                'volume_change_24h': market_data.get('total_volume_change_24h', 0),
                'social_score': self._calculate_social_score(community_data),
                'activity_score': 0  # Will be calculated below
            }
            
            # Calculate overall activity score
            activity_score = 0
            if abs(activity_data['price_change_24h']) > 5:  # Significant price movement
                activity_score += 20
            if abs(activity_data['volume_change_24h']) > 50:  # Significant volume change
                activity_score += 30
            if activity_data['social_score'] > 50:  # High social activity
                activity_score += 25
            
            activity_data['activity_score'] = min(activity_score, 100)
            
            # Cache the data
            self.cache[cache_key] = {
                'data': activity_data,
                'timestamp': current_time
            }
            
            return activity_data
            
        except Exception as e:
            logger.error(f"Error fetching network activity for {symbol}: {e}")
            return {}
    
    def _calculate_social_score(self, community_data: Dict) -> int:
        """Calculate a social activity score from community data"""
        try:
            score = 0
            
            # Twitter followers (normalized)
            twitter_followers = community_data.get('twitter_followers', 0)
            if twitter_followers > 100000:
                score += 30
            elif twitter_followers > 50000:
                score += 20
            elif twitter_followers > 10000:
                score += 10
            
            # Reddit subscribers
            reddit_subscribers = community_data.get('reddit_subscribers', 0)
            if reddit_subscribers > 50000:
                score += 25
            elif reddit_subscribers > 10000:
                score += 15
            elif reddit_subscribers > 1000:
                score += 5
            
            # Telegram users
            telegram_users = community_data.get('telegram_channel_user_count', 0)
            if telegram_users > 10000:
                score += 20
            elif telegram_users > 1000:
                score += 10
            
            # Facebook likes
            facebook_likes = community_data.get('facebook_likes', 0)
            if facebook_likes > 10000:
                score += 15
            elif facebook_likes > 1000:
                score += 5
            
            return min(score, 100)
            
        except Exception as e:
            logger.error(f"Error calculating social score: {e}")
            return 0

class DataManager:
    def __init__(self):
        self.exchanges = {
            'binanceus': ccxt.binanceus({'enableRateLimit': True}),
            'coinbase': ccxt.coinbasepro({'enableRateLimit': True}),
        }
        self.onchain_manager = OnChainDataManager()
        self.cache = {}
        self.cache_duration = 30  # seconds
    
    def get_market_data(self, symbol: str, timeframe: str = '5m', limit: int = 100, exchange: str = 'binanceus') -> pd.DataFrame:
        """Fetch market data with caching"""
        cache_key = f"{exchange}_{symbol}_{timeframe}"
        current_time = time.time()
        
        # Check cache
        if (cache_key in self.cache and 
            current_time - self.cache[cache_key]['timestamp'] < self.cache_duration):
            return self.cache[cache_key]['data']
        
        try:
            exchange_obj = self.exchanges[exchange]
            ohlcv = exchange_obj.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Cache the data
            self.cache[cache_key] = {
                'data': df,
                'timestamp': current_time
            }
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_multiple_timeframes(self, symbol: str, exchange: str = 'binanceus') -> Dict[str, pd.DataFrame]:
        """Get data for multiple timeframes"""
        timeframes = ['1m', '5m', '15m', '1h']
        data = {}
        
        for tf in timeframes:
            data[tf] = self.get_market_data(symbol, tf, exchange=exchange)
        
        return data

class FundamentalEventMonitor:
    def __init__(self):
        self.events_cache = {}
        self.cache_duration = 3600  # 1 hour
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TradingBot/1.0'
        })
    
    def get_upcoming_events(self, symbol: str, days_ahead: int = 7) -> List[Dict]:
        """Get upcoming fundamental events using free APIs"""
        try:
            cache_key = f"events_{symbol}_{days_ahead}"
            current_time = time.time()
            
            # Check cache
            if (cache_key in self.events_cache and 
                current_time - self.events_cache[cache_key]['timestamp'] < self.cache_duration):
                return self.events_cache[cache_key]['data']
            
            events = []
            
            # Get events from multiple free sources
            events.extend(self._get_coingecko_events(symbol))
            events.extend(self._get_coinmarketcap_events(symbol))
            events.extend(self._generate_estimated_events(symbol))
            
            # Filter events within the specified timeframe
            current_date = datetime.now()
            end_date = current_date + timedelta(days=days_ahead)
            
            filtered_events = [
                event for event in events 
                if current_date <= event['date'] <= end_date
            ]
            
            # Sort by date
            filtered_events.sort(key=lambda x: x['date'])
            
            # Cache the results
            self.events_cache[cache_key] = {
                'data': filtered_events,
                'timestamp': current_time
            }
            
            return filtered_events
            
        except Exception as e:
            logger.error(f"Error fetching events for {symbol}: {e}")
            return []
    
    def _get_coingecko_events(self, symbol: str) -> List[Dict]:
        """Get events from CoinGecko API"""
        try:
            # CoinGecko events endpoint (free tier has limited access)
            url = "https://api.coingecko.com/api/v3/events"
            params = {
                'country_code': '',
                'type': '',
                'page': 1,
                'upcoming_events_only': 'true'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            # CoinGecko free tier might not have events API access
            if response.status_code == 200:
                data = response.json()
                events = []
                
                for event in data.get('data', []):
                    # Try to match events to our symbol
                    if self._event_matches_symbol(event, symbol):
                        events.append({
                            'date': datetime.strptime(event.get('start_date', ''), '%Y-%m-%d'),
                            'event_type': event.get('type', 'unknown'),
                            'description': event.get('title', ''),
                            'impact': self._determine_event_impact(event.get('type', '')),
                            'confidence': 'medium',
                            'source': 'coingecko'
                        })
                
                return events
            
        except Exception as e:
            logger.debug(f"CoinGecko events not available: {e}")
        
        return []
    
    def _get_coinmarketcap_events(self, symbol: str) -> List[Dict]:
        """Get events from CoinMarketCap (limited free access)"""
        try:
            # This would require CMC API key for detailed events
            # For now, we'll return empty list as free tier is very limited
            return []
            
        except Exception as e:
            logger.debug(f"CoinMarketCap events not available: {e}")
            return []
    
    def _generate_estimated_events(self, symbol: str) -> List[Dict]:
        """Generate estimated events based on common crypto patterns"""
        try:
            current_time = datetime.now()
            events = []
            
            # Get coin info to estimate events
            coin_id = self._symbol_to_coingecko_id(symbol)
            if not coin_id:
                return events
            
            # Common crypto event patterns
            # Monthly/quarterly events (estimated)
            for i in range(1, 8):  # Next 7 days
                event_date = current_time + timedelta(days=i)
                
                # Weekly market cycles (Sundays often see different activity)
                if event_date.weekday() == 6:  # Sunday
                    events.append({
                        'date': event_date,
                        'event_type': 'weekly_cycle',
                        'description': f'{symbol} Weekly Market Cycle',
                        'impact': 'neutral',
                        'confidence': 'low',
                        'source': 'pattern'
                    })
                
                # Month-end effects
                if event_date.day >= 28:
                    events.append({
                        'date': event_date,
                        'event_type': 'month_end',
                        'description': f'{symbol} Month-end Trading Effects',
                        'impact': 'neutral',
                        'confidence': 'low',
                        'source': 'pattern'
                    })
            
            # Add some randomized events based on symbol characteristics
            major_cryptos = ['BTC', 'ETH', 'BNB']
            base_symbol = symbol.split('/')[0]
            
            if base_symbol in major_cryptos:
                # Major cryptos might have more institutional activity
                events.append({
                    'date': current_time + timedelta(days=3),
                    'event_type': 'institutional_activity',
                    'description': f'{symbol} Potential Institutional Activity',
                    'impact': 'bullish',
                    'confidence': 'low',
                    'source': 'estimate'
                })
            
            return events
            
        except Exception as e:
            logger.error(f"Error generating estimated events: {e}")
            return []
    
    def _event_matches_symbol(self, event: Dict, symbol: str) -> bool:
        """Check if an event matches our trading symbol"""
        try:
            base_symbol = symbol.split('/')[0].lower()
            event_title = event.get('title', '').lower()
            event_description = event.get('description', '').lower()
            
            # Simple keyword matching
            return (base_symbol in event_title or 
                    base_symbol in event_description)
            
        except Exception:
            return False
    
    def _determine_event_impact(self, event_type: str) -> str:
        """Determine the likely price impact of an event type"""
        bullish_events = [
            'mainnet', 'upgrade', 'listing', 'partnership', 
            'adoption', 'launch', 'integration', 'etf'
        ]
        bearish_events = [
            'unlock', 'dump', 'hack', 'regulation', 'ban', 'delisting'
        ]
        
        event_type_lower = event_type.lower()
        
        for bullish in bullish_events:
            if bullish in event_type_lower:
                return 'bullish'
        
        for bearish in bearish_events:
            if bearish in event_type_lower:
                return 'bearish'
        
        return 'neutral'
    
    def _symbol_to_coingecko_id(self, symbol: str) -> str:
        """Convert trading symbol to CoinGecko ID (reusing from OnChainDataManager)"""
        base_symbol = symbol.split('/')[0].upper()
        
        symbol_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'ADA': 'cardano',
            'SOL': 'solana',
            'XRP': 'ripple',
            'DOT': 'polkadot',
            'AVAX': 'avalanche-2',
            'MATIC': 'matic-network',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'LTC': 'litecoin',
            'BCH': 'bitcoin-cash',
            'ALGO': 'algorand',
            'VET': 'vechain',
            'FIL': 'filecoin',
            'TRX': 'tron',
            'ETC': 'ethereum-classic',
            'XLM': 'stellar',
            'ATOM': 'cosmos',
            'HBAR': 'hedera-hashgraph',
            'NEAR': 'near',
            'MANA': 'decentraland',
            'SAND': 'the-sandbox',
            'CRO': 'crypto-com-chain',
            'APE': 'apecoin',
            'LDO': 'lido-dao',
            'SHIB': 'shiba-inu'
        }
        
        return symbol_map.get(base_symbol, '')
    
    def check_event_impact(self, symbol: str) -> Dict:
        """Check if there are any impactful events in the next 24-48 hours"""
        try:
            events = self.get_upcoming_events(symbol, days_ahead=2)
            
            bullish_events = [e for e in events if e['impact'] == 'bullish']
            bearish_events = [e for e in events if e['impact'] == 'bearish']
            
            # Weight events by confidence
            bullish_score = sum(10 if e['confidence'] == 'high' else 5 if e['confidence'] == 'medium' else 2 for e in bullish_events)
            bearish_score = sum(10 if e['confidence'] == 'high' else 5 if e['confidence'] == 'medium' else 2 for e in bearish_events)
            
            return {
                'has_bullish_catalyst': len(bullish_events) > 0,
                'has_bearish_catalyst': len(bearish_events) > 0,
                'bullish_events': bullish_events,
                'bearish_events': bearish_events,
                'event_score': bullish_score - bearish_score
            }
        except Exception as e:
            logger.error(f"Error checking event impact for {symbol}: {e}")
            return {
                'has_bullish_catalyst': False,
                'has_bearish_catalyst': False,
                'bullish_events': [],
                'bearish_events': [],
                'event_score': 0
            }

class MarketSentimentAnalyzer:
    def __init__(self):
        self.sentiment_cache = {}
        self.cache_duration = 1800  # 30 minutes
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TradingBot/1.0'
        })
    
    def get_fear_greed_index(self) -> Dict:
        """Get crypto fear & greed index from free API"""
        try:
            cache_key = "fear_greed_index"
            current_time = time.time()
            
            # Check cache
            if (cache_key in self.sentiment_cache and 
                current_time - self.sentiment_cache[cache_key]['timestamp'] < self.cache_duration):
                return self.sentiment_cache[cache_key]['data']
            
            # Free Fear & Greed Index API
            url = "https://api.alternative.me/fng/"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                latest = data['data'][0]
                fear_greed_data = {
                    'value': int(latest.get('value', 50)),
                    'classification': latest.get('value_classification', 'Neutral'),
                    'trend': self._calculate_trend(data['data']) if len(data['data']) > 1 else 'stable',
                    'last_updated': latest.get('timestamp', '')
                }
            else:
                # Fallback data
                fear_greed_data = {
                    'value': 50,
                    'classification': 'Neutral',
                    'trend': 'stable',
                    'last_updated': str(int(time.time()))
                }
            
            # Cache the data
            self.sentiment_cache[cache_key] = {
                'data': fear_greed_data,
                'timestamp': current_time
            }
            
            return fear_greed_data
            
        except Exception as e:
            logger.error(f"Error fetching fear & greed index: {e}")
            return {
                'value': 50,
                'classification': 'Neutral',
                'trend': 'stable',
                'last_updated': str(int(time.time()))
            }
    
    def get_social_sentiment(self, symbol: str) -> Dict:
        """Get social media sentiment using free sources"""
        try:
            cache_key = f"social_sentiment_{symbol}"
            current_time = time.time()
            
            # Check cache
            if (cache_key in self.sentiment_cache and 
                current_time - self.sentiment_cache[cache_key]['timestamp'] < self.cache_duration):
                return self.sentiment_cache[cache_key]['data']
            
            # Get community data from CoinGecko as sentiment proxy
            sentiment_data = self._get_coingecko_community_sentiment(symbol)
            
            # Cache the data
            self.sentiment_cache[cache_key] = {
                'data': sentiment_data,
                'timestamp': current_time
            }
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Error fetching social sentiment for {symbol}: {e}")
            return {
                'sentiment_score': 0,
                'mention_count': 0,
                'trend': 'neutral',
                'social_dominance': 0
            }
    
    def _calculate_trend(self, fear_greed_history: List[Dict]) -> str:
        """Calculate trend from fear & greed historical data"""
        try:
            if len(fear_greed_history) < 2:
                return 'stable'
            
            current_value = int(fear_greed_history[0].get('value', 50))
            previous_value = int(fear_greed_history[1].get('value', 50))
            
            difference = current_value - previous_value
            
            if difference > 5:
                return 'increasing'
            elif difference < -5:
                return 'decreasing'
            else:
                return 'stable'
                
        except Exception:
            return 'stable'
    
    def _get_coingecko_community_sentiment(self, symbol: str) -> Dict:
        """Get community sentiment from CoinGecko community data"""
        try:
            coin_id = self._symbol_to_coingecko_id(symbol)
            if not coin_id:
                return {
                    'sentiment_score': 0,
                    'mention_count': 0,
                    'trend': 'neutral',
                    'social_dominance': 0
                }
            
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'true',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            community_data = data.get('community_data', {})
            market_data = data.get('market_data', {})
            
            # Calculate sentiment score from community metrics
            sentiment_score = self._calculate_sentiment_from_community(community_data, market_data)
            
            # Estimate mention count from community size
            mention_count = self._estimate_mention_count(community_data)
            
            # Determine trend from price movement
            price_change_24h = market_data.get('price_change_percentage_24h', 0)
            trend = 'positive' if price_change_24h > 2 else 'negative' if price_change_24h < -2 else 'neutral'
            
            # Calculate social dominance (normalized community size)
            social_dominance = self._calculate_social_dominance(community_data)
            
            return {
                'sentiment_score': sentiment_score,
                'mention_count': mention_count,
                'trend': trend,
                'social_dominance': social_dominance
            }
            
        except Exception as e:
            logger.error(f"Error fetching CoinGecko community sentiment: {e}")
            return {
                'sentiment_score': 0,
                'mention_count': 0,
                'trend': 'neutral',
                'social_dominance': 0
            }
    
    def _calculate_sentiment_from_community(self, community_data: Dict, market_data: Dict) -> float:
        """Calculate sentiment score from community and market data"""
        try:
            score = 0.0
            
            # Positive indicators
            twitter_followers = community_data.get('twitter_followers', 0)
            reddit_subscribers = community_data.get('reddit_subscribers', 0)
            telegram_users = community_data.get('telegram_channel_user_count', 0)
            
            # Community growth indicators (positive sentiment)
            if twitter_followers > 100000:
                score += 0.3
            elif twitter_followers > 10000:
                score += 0.1
            
            if reddit_subscribers > 50000:
                score += 0.2
            elif reddit_subscribers > 5000:
                score += 0.1
            
            if telegram_users > 10000:
                score += 0.2
            elif telegram_users > 1000:
                score += 0.1
            
            # Market sentiment from price action
            price_change_24h = market_data.get('price_change_percentage_24h', 0)
            volume_change_24h = market_data.get('total_volume_change_24h', 0)
            
            # Price momentum contributes to sentiment
            if price_change_24h > 5:
                score += 0.3
            elif price_change_24h > 0:
                score += 0.1
            elif price_change_24h < -5:
                score -= 0.3
            elif price_change_24h < 0:
                score -= 0.1
            
            # Volume change indicates engagement
            if volume_change_24h > 50:
                score += 0.2
            elif volume_change_24h > 0:
                score += 0.1
            
            # Normalize to -1 to 1 range
            return max(-1.0, min(1.0, score))
            
        except Exception:
            return 0.0
    
    def _estimate_mention_count(self, community_data: Dict) -> int:
        """Estimate social media mentions from community size"""
        try:
            twitter_followers = community_data.get('twitter_followers', 0)
            reddit_subscribers = community_data.get('reddit_subscribers', 0)
            
            # Rough estimation: larger communities = more mentions
            estimated_mentions = (twitter_followers * 0.01) + (reddit_subscribers * 0.05)
            return int(min(estimated_mentions, 10000))  # Cap at reasonable number
            
        except Exception:
            return 0
    
    def _calculate_social_dominance(self, community_data: Dict) -> float:
        """Calculate social dominance score (0-100)"""
        try:
            score = 0
            
            twitter_followers = community_data.get('twitter_followers', 0)
            reddit_subscribers = community_data.get('reddit_subscribers', 0)
            telegram_users = community_data.get('telegram_channel_user_count', 0)
            facebook_likes = community_data.get('facebook_likes', 0)
            
            # Score based on community size thresholds
            if twitter_followers > 1000000:
                score += 30
            elif twitter_followers > 100000:
                score += 20
            elif twitter_followers > 10000:
                score += 10
            
            if reddit_subscribers > 100000:
                score += 25
            elif reddit_subscribers > 10000:
                score += 15
            elif reddit_subscribers > 1000:
                score += 5
            
            if telegram_users > 50000:
                score += 20
            elif telegram_users > 5000:
                score += 10
            
            if facebook_likes > 50000:
                score += 15
            elif facebook_likes > 5000:
                score += 5
            
            return min(score, 100)
            
        except Exception:
            return 0
    
    def _symbol_to_coingecko_id(self, symbol: str) -> str:
        """Convert trading symbol to CoinGecko ID"""
        base_symbol = symbol.split('/')[0].upper()
        
        symbol_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'ADA': 'cardano',
            'SOL': 'solana',
            'XRP': 'ripple',
            'DOT': 'polkadot',
            'AVAX': 'avalanche-2',
            'MATIC': 'matic-network',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'LTC': 'litecoin',
            'BCH': 'bitcoin-cash',
            'ALGO': 'algorand',
            'VET': 'vechain',
            'FIL': 'filecoin',
            'TRX': 'tron',
            'ETC': 'ethereum-classic',
            'XLM': 'stellar',
            'ATOM': 'cosmos',
            'HBAR': 'hedera-hashgraph',
            'NEAR': 'near',
            'MANA': 'decentraland',
            'SAND': 'the-sandbox',
            'CRO': 'crypto-com-chain',
            'APE': 'apecoin',
            'LDO': 'lido-dao',
            'SHIB': 'shiba-inu'
        }
        
        return symbol_map.get(base_symbol, '')
    
    def get_market_sentiment_summary(self) -> Dict:
        """Get overall market sentiment summary"""
        try:
            fear_greed = self.get_fear_greed_index()
            
            # Get sentiment for major cryptos
            btc_sentiment = self.get_social_sentiment('BTC/USDT')
            eth_sentiment = self.get_social_sentiment('ETH/USDT')
            
            # Calculate overall market sentiment
            overall_sentiment = (
                (fear_greed['value'] - 50) / 50 * 0.5 +  # Fear/Greed contributes 50%
                btc_sentiment['sentiment_score'] * 0.3 +    # BTC sentiment 30%
                eth_sentiment['sentiment_score'] * 0.2      # ETH sentiment 20%
            )
            
            return {
                'overall_sentiment': overall_sentiment,
                'fear_greed_index': fear_greed['value'],
                'fear_greed_classification': fear_greed['classification'],
                'btc_sentiment': btc_sentiment['sentiment_score'],
                'eth_sentiment': eth_sentiment['sentiment_score'],
                'market_mood': self._classify_market_mood(overall_sentiment)
            }
            
        except Exception as e:
            logger.error(f"Error getting market sentiment summary: {e}")
            return {
                'overall_sentiment': 0,
                'fear_greed_index': 50,
                'fear_greed_classification': 'Neutral',
                'btc_sentiment': 0,
                'eth_sentiment': 0,
                'market_mood': 'neutral'
            }
    
    def _classify_market_mood(self, sentiment_score: float) -> str:
        """Classify market mood based on sentiment score"""
        if sentiment_score > 0.5:
            return 'euphoric'
        elif sentiment_score > 0.2:
            return 'optimistic'
        elif sentiment_score > -0.2:
            return 'neutral'
        elif sentiment_score > -0.5:
            return 'pessimistic'
        else:
            return 'fearful'

# Add these to the SignalGenerator class
class SignalGenerator:
    def __init__(self):
        self.analyzer = TechnicalAnalyzer()
        self.event_monitor = FundamentalEventMonitor()
        self.sentiment_analyzer = MarketSentimentAnalyzer()
    
    def generate_signals(self, symbol: str, data: Dict[str, pd.DataFrame]) -> List[MarketSignal]:
        """Generate trading signals based on multi-factor analysis"""
        signals = []
        
        try:
            # Primary analysis on 5m chart
            df_5m = data.get('5m')
            df_1m = data.get('1m')
            df_15m = data.get('15m')
            
            if df_5m is None or len(df_5m) < 50:
                return signals
            
            # Calculate technical indicators
            indicators_5m = self.analyzer.calculate_all_indicators(df_5m)
            indicators_1m = self.analyzer.calculate_all_indicators(df_1m) if df_1m is not None and len(df_1m) >= 50 else {}
            
            # Get on-chain data (now using real free APIs)
            onchain_data = {}
            try:
                # Get exchange flows and network activity
                exchange_flows = self.data_manager.onchain_manager.get_exchange_flows(symbol)
                network_activity = self.data_manager.onchain_manager.get_network_activity(symbol)
                
                onchain_data = {
                    **exchange_flows,
                    'network_activity_score': network_activity.get('activity_score', 0),
                    'social_score': network_activity.get('social_score', 0)
                }
            except Exception as e:
                logger.error(f"Error fetching on-chain data for {symbol}: {e}")
            
            # Get fundamental events (now using real free APIs)
            event_data = self.event_monitor.check_event_impact(symbol)
            
            # Get sentiment data (now using real free APIs)
            sentiment_data = self.sentiment_analyzer.get_social_sentiment(symbol)
            fear_greed = self.sentiment_analyzer.get_fear_greed_index()
            
            # Generate bullish signals with enhanced scoring
            bullish_score = self._calculate_enhanced_bullish_score(
                indicators_5m, indicators_1m, onchain_data, event_data, sentiment_data, fear_greed
            )
            
            if bullish_score > 40:
                signal = self._create_enhanced_bullish_signal(symbol, indicators_5m, bullish_score, event_data)
                if signal:
                    signals.append(signal)
            
            # Generate bearish signals with enhanced scoring
            bearish_score = self._calculate_enhanced_bearish_score(
                indicators_5m, indicators_1m, onchain_data, event_data, sentiment_data, fear_greed
            )
            
            if bearish_score > 40:
                signal = self._create_enhanced_bearish_signal(symbol, indicators_5m, bearish_score, event_data)
                if signal:
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals for {symbol}: {e}")
            return []
    
    def _calculate_enhanced_bullish_score(self, ind_5m: Dict, ind_1m: Dict, onchain_data: Dict, 
                                        event_data: Dict, sentiment_data: Dict, fear_greed: Dict) -> float:
        """Enhanced bullish scoring with all data sources"""
        score = 0
        
        # Technical Analysis (50% weight)
        tech_score = self._calculate_bullish_score(ind_5m, ind_1m, onchain_data)
        score += tech_score * 0.5
        
        # Fundamental Events (25% weight)
        if event_data.get('has_bullish_catalyst', False):
            score += 20
        if event_data.get('event_score', 0) > 0:
            score += min(event_data['event_score'], 15)
        
        # Market Sentiment (15% weight)
        if sentiment_data.get('sentiment_score', 0) > 0.1:
            score += 10
        if sentiment_data.get('trend') == 'positive':
            score += 5
        
        # Fear & Greed Contrarian (10% weight)
        fg_value = fear_greed.get('value', 50)
        if fg_value < 25:  # Extreme fear - contrarian bullish
            score += 10
        elif fg_value < 40:  # Fear - somewhat bullish
            score += 5
        elif fg_value > 80:  # Extreme greed - caution
            score -= 5
        
        return min(score, 100)
    
    def _calculate_enhanced_bearish_score(self, ind_5m: Dict, ind_1m: Dict, onchain_data: Dict, 
                                        event_data: Dict, sentiment_data: Dict, fear_greed: Dict) -> float:
        """Enhanced bearish scoring with all data sources"""
        score = 0
        
        # Technical Analysis (50% weight)
        tech_score = self._calculate_bearish_score(ind_5m, ind_1m, onchain_data)
        score += tech_score * 0.5
        
        # Fundamental Events (25% weight)
        if event_data.get('has_bearish_catalyst', False):
            score += 20
        if event_data.get('event_score', 0) < 0:
            score += min(abs(event_data['event_score']), 15)
        
        # Market Sentiment (15% weight)
        if sentiment_data.get('sentiment_score', 0) < -0.1:
            score += 10
        if sentiment_data.get('trend') == 'negative':
            score += 5
        
        # Fear & Greed Contrarian (10% weight)
        fg_value = fear_greed.get('value', 50)
        if fg_value > 80:  # Extreme greed - contrarian bearish
            score += 10
        elif fg_value > 65:  # Greed - somewhat bearish
            score += 5
        
        return min(score, 100)
    
    def _calculate_bullish_score(self, ind_5m: Dict, ind_1m: Dict, onchain_data: Dict = None) -> float:
        """Calculate bullish signal strength with on-chain data"""
        score = 0
        
        # Technical Analysis (70% weight)
        # RSI signals
        if ind_5m.get('rsi', 50) > 50 and ind_5m.get('rsi', 50) < 70:
            score += 8
        if ind_5m.get('rsi_divergence', False):
            score += 15
        if ind_5m.get('rsi_oversold', False):
            score += 12
        
        # MACD signals
        if ind_5m.get('macd_bullish', False):
            score += 12
        
        # EMA alignment
        if ind_5m.get('ema_bullish_alignment', False):
            score += 8
        if ind_5m.get('price_above_ema21', False):
            score += 4
        
        # Enhanced Volume Analysis (based on methodology + PHASE 1 ENHANCEMENTS)
        # Phase 1 Volume Score Integration
        volume_phase1_score = ind_5m.get('volume_phase1_score', 0)
        score += volume_phase1_score  # Direct boost from Phase 1 patterns
        
        # Legacy volume patterns (keep for compatibility)
        if ind_5m.get('volume_spike_5x', False):  # Extreme volume spike
            score += 20
        elif ind_5m.get('volume_spike_3x', False):  # Strong volume spike
            score += 15
        elif ind_5m.get('volume_surge', False):  # Regular volume surge
            score += 10
        
        # NEW Phase 1 Volume Pattern Bonuses
        if ind_5m.get('sustained_volume', False):  # 3+ consecutive high volume bars
            score += 8
        if ind_5m.get('volume_acceleration', False):  # Accelerating volume pattern
            score += 6
        if ind_5m.get('volume_breakout', False):  # Highest volume in 20 periods
            score += 12
        if ind_5m.get('smart_money_volume', False):  # High volume + small price change
            score += 10
        
        # Volume momentum and trend
        if ind_5m.get('volume_momentum', 1) > 1.5:
            score += 8
        if ind_5m.get('volume_trend_increasing', False):
            score += 5
        
        # Bollinger Bands
        if ind_5m.get('bb_squeeze', False):
            score += 8
        if ind_5m.get('bb_position') == 'lower':
            score += 8
        
        # Breakout
        if ind_5m.get('breakout_up', False):
            score += 15
        
        # Support/Resistance
        if ind_5m.get('near_support', False):
            score += 8
        
        # On-Chain Analysis (30% weight) - NEW
        if onchain_data:
            # Exchange outflows (accumulation)
            if onchain_data.get('net_flow', 0) < -1000000:  # Large outflows
                score += 15
            elif onchain_data.get('net_flow', 0) < 0:  # Any outflows
                score += 8
            
            # Whale activity
            if onchain_data.get('whale_activity', False):
                score += 12
            
            # Smart money flows
            smart_flow = onchain_data.get('smart_money_flow', 0)
            if smart_flow > 0:
                score += 10
        
        return min(score, 100)
    
    def _calculate_bearish_score(self, ind_5m: Dict, ind_1m: Dict, onchain_data: Dict = None) -> float:
        """Calculate bearish signal strength with on-chain data"""
        score = 0
        
        # Technical Analysis (70% weight)
        # RSI signals
        if ind_5m.get('rsi', 50) < 50:
            score += 8
        if ind_5m.get('rsi_overbought', False):
            score += 12
        
        # MACD signals
        if not ind_5m.get('macd_bullish', True):
            score += 12
        
        # EMA alignment
        if not ind_5m.get('ema_bullish_alignment', True):
            score += 8
        if not ind_5m.get('price_above_ema21', True):
            score += 4
        
        # Enhanced Volume Analysis
        if ind_5m.get('volume_spike_5x', False) and ind_5m.get('price_change_pct', 0) < 0:
            score += 20  # Extreme selling volume
        elif ind_5m.get('volume_spike_3x', False) and ind_5m.get('price_change_pct', 0) < 0:
            score += 15  # Strong selling volume
        elif ind_5m.get('volume_surge', False) and ind_5m.get('price_change_pct', 0) < 0:
            score += 12  # Regular selling volume
        
        # Bollinger Bands
        if ind_5m.get('bb_position') == 'upper':
            score += 8
        
        # Breakdown
        if ind_5m.get('breakdown', False):
            score += 15
        
        # Resistance
        if ind_5m.get('near_resistance', False):
            score += 8
        
        # On-Chain Analysis (30% weight) - NEW
        if onchain_data:
            # Exchange inflows (selling pressure)
            if onchain_data.get('net_flow', 0) > 1000000:  # Large inflows
                score += 15
            elif onchain_data.get('net_flow', 0) > 0:  # Any inflows
                score += 8
            
            # Smart money selling
            smart_flow = onchain_data.get('smart_money_flow', 0)
            if smart_flow < 0:
                score += 10
        
        return min(score, 100)
    
    def _create_enhanced_bullish_signal(self, symbol: str, indicators: Dict, score: float, event_data: Dict) -> Optional[MarketSignal]:
        """Create an enhanced bullish trading signal with fundamental context"""
        try:
            current_price = indicators['current_price']
            atr = indicators['atr']
            
            # Calculate stop loss and take profit
            stop_loss = current_price - (atr * 1.5)
            take_profit = current_price + (atr * 3)
            risk_reward = (take_profit - current_price) / (current_price - stop_loss)
            
            # Enhanced confidence determination
            if score >= 85:
                confidence = 'critical'
            elif score >= 75:
                confidence = 'high'
            elif score >= 60:
                confidence = 'medium'
            else:
                confidence = 'low'
            
            # Add event context to indicators
            enhanced_indicators = indicators.copy()
            enhanced_indicators['fundamental_events'] = event_data.get('bullish_events', [])
            enhanced_indicators['event_score'] = event_data.get('event_score', 0)
            
            return MarketSignal(
                symbol=symbol,
                timeframe='5m',
                signal_type='bullish_entry',
                strength=score,
                direction='bullish',
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward=risk_reward,
                confidence=confidence,
                indicators=enhanced_indicators,
                timestamp=datetime.now()
            )
        except:
            return None
    
    def _create_enhanced_bearish_signal(self, symbol: str, indicators: Dict, score: float, event_data: Dict) -> Optional[MarketSignal]:
        """Create an enhanced bearish trading signal with fundamental context"""
        try:
            current_price = indicators['current_price']
            atr = indicators['atr']
            
            # Calculate stop loss and take profit for short
            stop_loss = current_price + (atr * 1.5)
            take_profit = current_price - (atr * 3)
            risk_reward = (current_price - take_profit) / (stop_loss - current_price)
            
            # Enhanced confidence determination
            if score >= 85:
                confidence = 'critical'
            elif score >= 75:
                confidence = 'high'
            elif score >= 60:
                confidence = 'medium'
            else:
                confidence = 'low'
            
            # Add event context to indicators
            enhanced_indicators = indicators.copy()
            enhanced_indicators['fundamental_events'] = event_data.get('bearish_events', [])
            enhanced_indicators['event_score'] = event_data.get('event_score', 0)
            
            return MarketSignal(
                symbol=symbol,
                timeframe='5m',
                signal_type='bearish_entry',
                strength=score,
                direction='bearish',
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward=risk_reward,
                confidence=confidence,
                indicators=enhanced_indicators,
                timestamp=datetime.now()
            )
        except:
            return None

class TradingBotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Local Day Trading Analysis Bot")
        self.root.geometry("1400x900")
        
        # Initialize components
        self.data_manager = DataManager()
        self.signal_generator = SignalGenerator()
        
        # Configuration
        self.config = self.load_config()
        self.watchlist = self.config.get('watchlist', [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT',
            'SOL/USDT', 'XRP/USDT', 'DOT/USDT', 'AVAX/USDT'
        ])
        
        # State
        self.signals = []
        self.running = False
        self.scan_thread = None
        
        self.setup_gui()
        self.start_scanning()
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        config_file = 'trading_config.json'
        default_config = {
            'scan_interval': 30,
            'min_signal_strength': 50,
            'sound_alerts': True,
            'desktop_notifications': True,
            'watchlist': [
                'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT',
                'SOL/USDT', 'XRP/USDT', 'DOT/USDT', 'AVAX/USDT'
            ]
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        return default_config
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open('trading_config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def setup_gui(self):
        """Setup the GUI components"""
        # Create main frames
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Control panel
        self.setup_control_panel(control_frame)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        
        # Signals tab
        signals_frame = ttk.Frame(notebook)
        notebook.add(signals_frame, text='Live Signals')
        self.setup_signals_tab(signals_frame)
        
        # Market overview tab
        market_frame = ttk.Frame(notebook)
        notebook.add(market_frame, text='Market Overview')
        self.setup_market_tab(market_frame)
        
        # Configuration tab
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text='Configuration')
        self.setup_config_tab(config_frame)
        
        # On-chain & Sentiment tab (NEW)
        onchain_frame = ttk.Frame(notebook)
        notebook.add(onchain_frame, text='On-Chain & Sentiment')
        self.setup_onchain_tab(onchain_frame)
    
    def setup_control_panel(self, parent):
        """Setup control panel"""
        # Status
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(parent, textvariable=self.status_var, font=('Arial', 10, 'bold'))
        status_label.pack(side='left', padx=10)
        
        # Start/Stop button
        self.start_button = ttk.Button(parent, text="Start Scanning", command=self.toggle_scanning)
        self.start_button.pack(side='left', padx=10)
        
        # Manual scan button
        manual_scan_button = ttk.Button(parent, text="Manual Scan", command=self.manual_scan)
        manual_scan_button.pack(side='left', padx=10)
        
        # Last update time
        self.last_update_var = tk.StringVar(value="Never")
        update_label = ttk.Label(parent, text="Last Update:")
        update_label.pack(side='right', padx=5)
        update_time_label = ttk.Label(parent, textvariable=self.last_update_var)
        update_time_label.pack(side='right', padx=5)
    
    def setup_signals_tab(self, parent):
        """Setup signals display tab"""
        # Signals treeview
        columns = ('Symbol', 'Direction', 'Strength', 'Confidence', 'Entry', 'Stop Loss', 'Take Profit', 'R:R', 'Time')
        self.signals_tree = ttk.Treeview(parent, columns=columns, show='headings', height=15)
        
        # Configure columns
        widths = [80, 80, 80, 80, 100, 100, 100, 60, 120]
        for col, width in zip(columns, widths):
            self.signals_tree.heading(col, text=col)
            self.signals_tree.column(col, width=width)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=self.signals_tree.yview)
        self.signals_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.signals_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind double-click event
        self.signals_tree.bind('<Double-1>', self.on_signal_double_click)
    
    def setup_market_tab(self, parent):
        """Setup market overview tab"""
        # Create frame for market data
        market_data_frame = ttk.LabelFrame(parent, text="Market Overview")
        market_data_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Market data treeview
        market_columns = ('Symbol', 'Price', 'Change %', 'Volume', 'RSI', 'MACD', 'BB Position', 'Signal')
        self.market_tree = ttk.Treeview(market_data_frame, columns=market_columns, show='headings', height=20)
        
        # Configure market columns
        market_widths = [80, 100, 80, 120, 60, 80, 80, 100]
        for col, width in zip(market_columns, market_widths):
            self.market_tree.heading(col, text=col)
            self.market_tree.column(col, width=width)
        
        # Market scrollbar
        market_scrollbar = ttk.Scrollbar(market_data_frame, orient='vertical', command=self.market_tree.yview)
        self.market_tree.configure(yscrollcommand=market_scrollbar.set)
        
        # Pack market treeview
        self.market_tree.pack(side='left', fill='both', expand=True)
        market_scrollbar.pack(side='right', fill='y')
    
    def setup_config_tab(self, parent):
        """Setup configuration tab"""
        # Scan interval
        interval_frame = ttk.LabelFrame(parent, text="Scan Settings")
        interval_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(interval_frame, text="Scan Interval (seconds):").pack(side='left', padx=5)
        self.interval_var = tk.StringVar(value=str(self.config.get('scan_interval', 30)))
        interval_entry = ttk.Entry(interval_frame, textvariable=self.interval_var, width=10)
        interval_entry.pack(side='left', padx=5)
        
        # Minimum signal strength
        ttk.Label(interval_frame, text="Min Signal Strength:").pack(side='left', padx=5)
        self.min_strength_var = tk.StringVar(value=str(self.config.get('min_signal_strength', 50)))
        strength_entry = ttk.Entry(interval_frame, textvariable=self.min_strength_var, width=10)
        strength_entry.pack(side='left', padx=5)
        
        # Alert settings
        alert_frame = ttk.LabelFrame(parent, text="Alert Settings")
        alert_frame.pack(fill='x', padx=5, pady=5)
        
        self.sound_alerts_var = tk.BooleanVar(value=self.config.get('sound_alerts', True))
        sound_check = ttk.Checkbutton(alert_frame, text="Sound Alerts", variable=self.sound_alerts_var)
        sound_check.pack(side='left', padx=10)
        
        self.desktop_notifications_var = tk.BooleanVar(value=self.config.get('desktop_notifications', True))
        desktop_check = ttk.Checkbutton(alert_frame, text="Desktop Notifications", variable=self.desktop_notifications_var)
        desktop_check.pack(side='left', padx=10)
        
        # Watchlist
        watchlist_frame = ttk.LabelFrame(parent, text="Watchlist")
        watchlist_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Watchlist listbox
        self.watchlist_var = tk.StringVar(value=self.watchlist)
        watchlist_listbox = tk.Listbox(watchlist_frame, listvariable=self.watchlist_var, height=10)
        watchlist_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Save config button
        save_button = ttk.Button(parent, text="Save Configuration", command=self.save_configuration)
        save_button.pack(pady=10)
    
    def setup_onchain_tab(self, parent):
        """Setup on-chain and sentiment data tab"""
        # Market sentiment frame
        sentiment_frame = ttk.LabelFrame(parent, text="Market Sentiment")
        sentiment_frame.pack(fill='x', padx=5, pady=5)
        
        # Fear & Greed Index
        self.fear_greed_var = tk.StringVar(value="Loading...")
        ttk.Label(sentiment_frame, text="Fear & Greed Index:").pack(side='left', padx=5)
        ttk.Label(sentiment_frame, textvariable=self.fear_greed_var).pack(side='left', padx=5)
        
        # Market mood
        self.market_mood_var = tk.StringVar(value="Loading...")
        ttk.Label(sentiment_frame, text="Market Mood:").pack(side='left', padx=15)
        ttk.Label(sentiment_frame, textvariable=self.market_mood_var).pack(side='left', padx=5)
        
        # On-chain data frame
        onchain_data_frame = ttk.LabelFrame(parent, text="On-Chain Data")
        onchain_data_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # On-chain data treeview
        onchain_columns = ('Symbol', 'Exchange Flows', 'Whale Activity', 'Social Score', 'Network Activity', 'Sentiment')
        self.onchain_tree = ttk.Treeview(onchain_data_frame, columns=onchain_columns, show='headings', height=15)
        
        # Configure onchain columns
        onchain_widths = [80, 120, 100, 100, 120, 100]
        for col, width in zip(onchain_columns, onchain_widths):
            self.onchain_tree.heading(col, text=col)
            self.onchain_tree.column(col, width=width)
        
        # Onchain scrollbar
        onchain_scrollbar = ttk.Scrollbar(onchain_data_frame, orient='vertical', command=self.onchain_tree.yview)
        self.onchain_tree.configure(yscrollcommand=onchain_scrollbar.set)
        
        # Pack onchain treeview
        self.onchain_tree.pack(side='left', fill='both', expand=True)
        onchain_scrollbar.pack(side='right', fill='y')
        
        # Stablecoin flows frame
        stablecoin_frame = ttk.LabelFrame(parent, text="Stablecoin Flows (24h)")
        stablecoin_frame.pack(fill='x', padx=5, pady=5)
        
        self.usdt_flow_var = tk.StringVar(value="USDT: Loading...")
        self.usdc_flow_var = tk.StringVar(value="USDC: Loading...")
        self.total_flow_var = tk.StringVar(value="Total: Loading...")
        
        ttk.Label(stablecoin_frame, textvariable=self.usdt_flow_var).pack(side='left', padx=10)
        ttk.Label(stablecoin_frame, textvariable=self.usdc_flow_var).pack(side='left', padx=10)
        ttk.Label(stablecoin_frame, textvariable=self.total_flow_var).pack(side='left', padx=10)
    
    def save_configuration(self):
        """Save current configuration"""
        try:
            self.config['scan_interval'] = int(self.interval_var.get())
            self.config['min_signal_strength'] = int(self.min_strength_var.get())
            self.config['sound_alerts'] = self.sound_alerts_var.get()
            self.config['desktop_notifications'] = self.desktop_notifications_var.get()
            self.save_config()
            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving configuration: {e}")
    
    def toggle_scanning(self):
        """Start or stop scanning"""
        if not self.running:
            self.start_scanning()
        else:
            self.stop_scanning()
    
    def start_scanning(self):
        """Start the scanning process"""
        if not self.running:
            self.running = True
            self.start_button.config(text="Stop Scanning")
            self.status_var.set("Scanning...")
            
            # Start scanning thread
            self.scan_thread = threading.Thread(target=self.scan_loop, daemon=True)
            self.scan_thread.start()
    
    def stop_scanning(self):
        """Stop the scanning process"""
        self.running = False
        self.start_button.config(text="Start Scanning")
        self.status_var.set("Stopped")
    
    def scan_loop(self):
        """Main scanning loop"""
        while self.running:
            try:
                self.perform_scan()
                time.sleep(self.config.get('scan_interval', 30))
            except Exception as e:
                logger.error(f"Error in scan loop: {e}")
                time.sleep(5)
    
    def perform_scan(self):
        """Perform a single scan of all watchlist symbols"""
        try:
            new_signals = []
            market_data = []
            onchain_data_list = []
            
            for symbol in self.watchlist:
                try:
                    # Get multi-timeframe data
                    data = self.data_manager.get_multiple_timeframes(symbol)
                    
                    # Generate signals
                    signals = self.signal_generator.generate_signals(symbol, data)
                    
                    # Filter signals by minimum strength
                    min_strength = self.config.get('min_signal_strength', 50)
                    filtered_signals = [s for s in signals if s.strength >= min_strength]
                    new_signals.extend(filtered_signals)
                    
                    # Collect market data
                    if '5m' in data and not data['5m'].empty:
                        indicators = self.signal_generator.analyzer.calculate_all_indicators(data['5m'])
                        if indicators:
                            market_info = {
                                'symbol': symbol,
                                'price': indicators.get('current_price', 0),
                                'change_pct': indicators.get('price_change_pct', 0),
                                'volume': indicators.get('current_volume', 0),
                                'rsi': indicators.get('rsi', 50),
                                'macd_bullish': indicators.get('macd_bullish', False),
                                'bb_position': indicators.get('bb_position', 'middle'),
                                'has_signal': len(filtered_signals) > 0
                            }
                            market_data.append(market_info)
                    
                    # Collect on-chain data (NEW)
                    try:
                        exchange_flows = self.data_manager.onchain_manager.get_exchange_flows(symbol)
                        network_activity = self.data_manager.onchain_manager.get_network_activity(symbol)
                        social_sentiment = self.signal_generator.sentiment_analyzer.get_social_sentiment(symbol)
                        
                        onchain_info = {
                            'symbol': symbol,
                            'net_flow': exchange_flows.get('net_flow', 0),
                            'whale_activity': exchange_flows.get('whale_activity', False),
                            'social_score': network_activity.get('social_score', 0),
                            'activity_score': network_activity.get('activity_score', 0),
                            'sentiment_score': social_sentiment.get('sentiment_score', 0)
                        }
                        onchain_data_list.append(onchain_info)
                    except Exception as e:
                        logger.error(f"Error collecting on-chain data for {symbol}: {e}")
                    
                except Exception as e:
                    logger.error(f"Error scanning {symbol}: {e}")
                    continue
            
            # Update GUI
            self.root.after(0, self.update_signals_display, new_signals)
            self.root.after(0, self.update_market_display, market_data)
            self.root.after(0, self.update_onchain_display, onchain_data_list)
            self.root.after(0, self.update_status)
            
            # Send alerts for new high-confidence signals
            for signal in new_signals:
                if signal.confidence in ['high', 'critical']:
                    self.root.after(0, self.send_alert, signal)
            
        except Exception as e:
            logger.error(f"Error in perform_scan: {e}")
    
    def manual_scan(self):
        """Perform a manual scan"""
        if not self.running:
            threading.Thread(target=self.perform_scan, daemon=True).start()
    
    def update_signals_display(self, new_signals: List[MarketSignal]):
        """Update the signals display"""
        # Add new signals to the list
        self.signals.extend(new_signals)
        
        # Keep only last 50 signals
        self.signals = self.signals[-50:]
        
        # Clear existing items
        for item in self.signals_tree.get_children():
            self.signals_tree.delete(item)
        
        # Add signals to tree (newest first)
        for signal in reversed(self.signals):
            # Color coding based on confidence
            tags = []
            if signal.confidence == 'critical':
                tags = ['critical']
            elif signal.confidence == 'high':
                tags = ['high']
            elif signal.confidence == 'medium':
                tags = ['medium']
            else:
                tags = ['low']
            
            self.signals_tree.insert('', 'end', values=(
                signal.symbol,
                signal.direction.upper(),
                f"{signal.strength:.1f}%",
                signal.confidence.upper(),
                f"${signal.entry_price:.4f}",
                f"${signal.stop_loss:.4f}",
                f"${signal.take_profit:.4f}",
                f"{signal.risk_reward:.1f}:1",
                signal.timestamp.strftime('%H:%M:%S')
            ), tags=tags)
        
        # Configure tag colors
        self.signals_tree.tag_configure('critical', background='#ffcccc')
        self.signals_tree.tag_configure('high', background='#ffffcc')
        self.signals_tree.tag_configure('medium', background='#ccffcc')
        self.signals_tree.tag_configure('low', background='#f0f0f0')
    
    def update_market_display(self, market_data: List[Dict]):
        """Update the market overview display"""
        # Clear existing items
        for item in self.market_tree.get_children():
            self.market_tree.delete(item)
        
        # Add market data to tree
        for data in market_data:
            # Determine signal indicator
            signal_indicator = "🔥" if data['has_signal'] else "📊"
            
            # MACD indicator
            macd_indicator = "✅" if data['macd_bullish'] else "❌"
            
            self.market_tree.insert('', 'end', values=(
                data['symbol'],
                f"${data['price']:.4f}",
                f"{data['change_pct']:+.2f}%",
                f"{data['volume']:,.0f}",
                f"{data['rsi']:.1f}",
                macd_indicator,
                data['bb_position'].upper(),
                signal_indicator
            ))
    
    def update_onchain_display(self, onchain_data_list: List[Dict]):
        """Update the on-chain data display"""
        try:
            # Update sentiment indicators
            fear_greed = self.signal_generator.sentiment_analyzer.get_fear_greed_index()
            market_sentiment = self.signal_generator.sentiment_analyzer.get_market_sentiment_summary()
            
            self.fear_greed_var.set(f"{fear_greed.get('value', 50)} - {fear_greed.get('classification', 'Neutral')}")
            self.market_mood_var.set(market_sentiment.get('market_mood', 'neutral').title())
            
            # Update stablecoin flows
            stablecoin_flows = self.data_manager.onchain_manager.get_stablecoin_flows()
            self.usdt_flow_var.set(f"USDT: ${stablecoin_flows.get('usdt_inflow', 0):,.0f}")
            self.usdc_flow_var.set(f"USDC: ${stablecoin_flows.get('usdc_inflow', 0):,.0f}")
            self.total_flow_var.set(f"Total: ${stablecoin_flows.get('total_inflow_24h', 0):,.0f}")
            
            # Clear existing on-chain data
            for item in self.onchain_tree.get_children():
                self.onchain_tree.delete(item)
            
            # Add on-chain data to tree
            for data in onchain_data_list:
                # Format exchange flows
                net_flow = data.get('net_flow', 0)
                if net_flow > 0:
                    flow_indicator = f"📈 +${abs(net_flow):,.0f}"  # Inflows
                elif net_flow < 0:
                    flow_indicator = f"📉 -${abs(net_flow):,.0f}"  # Outflows
                else:
                    flow_indicator = "➖ $0"
                
                # Whale activity indicator
                whale_indicator = "🐋" if data.get('whale_activity', False) else "🐟"
                
                # Social score
                social_score = data.get('social_score', 0)
                social_indicator = f"{social_score}/100"
                
                # Network activity
                activity_score = data.get('activity_score', 0)
                activity_indicator = f"{activity_score}/100"
                
                # Sentiment
                sentiment_score = data.get('sentiment_score', 0)
                if sentiment_score > 0.2:
                    sentiment_indicator = "😊 Positive"
                elif sentiment_score < -0.2:
                    sentiment_indicator = "😔 Negative"
                else:
                    sentiment_indicator = "😐 Neutral"
                
                self.onchain_tree.insert('', 'end', values=(
                    data['symbol'],
                    flow_indicator,
                    whale_indicator,
                    social_indicator,
                    activity_indicator,
                    sentiment_indicator
                ))
                
        except Exception as e:
            logger.error(f"Error updating on-chain display: {e}")
    
    def update_status(self):
        """Update status information"""
        self.last_update_var.set(datetime.now().strftime('%H:%M:%S'))
        
        # Count active signals by confidence
        signal_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        recent_signals = [s for s in self.signals if (datetime.now() - s.timestamp).seconds < 300]  # Last 5 minutes
        
        for signal in recent_signals:
            signal_counts[signal.confidence] += 1
        
        status_text = f"Active - Critical: {signal_counts['critical']}, High: {signal_counts['high']}, Medium: {signal_counts['medium']}"
        self.status_var.set(status_text)
    
    def send_alert(self, signal: MarketSignal):
        """Send alert notifications"""
        try:
            # Desktop notification
            if self.config.get('desktop_notifications', True):
                title = f"🚨 {signal.confidence.upper()} SIGNAL"
                message = f"{signal.symbol} - {signal.direction.upper()}\nStrength: {signal.strength:.1f}%\nEntry: ${signal.entry_price:.4f}"
                
                notification.notify(
                    title=title,
                    message=message,
                    timeout=10
                )
            
            # Sound alert
            if self.config.get('sound_alerts', True):
                try:
                    # Play different sounds based on confidence
                    if signal.confidence == 'critical':
                        winsound.Beep(2000, 500)  # High pitch, long beep
                    elif signal.confidence == 'high':
                        winsound.Beep(1500, 300)  # Medium pitch, medium beep
                    else:
                        winsound.Beep(1000, 200)  # Low pitch, short beep
                except:
                    pass  # Ignore sound errors on non-Windows systems
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def on_signal_double_click(self, event):
        """Handle double-click on signal"""
        selection = self.signals_tree.selection()
        if selection:
            item = self.signals_tree.item(selection[0])
            symbol = item['values'][0]
            self.show_detailed_analysis(symbol)
    
    def show_detailed_analysis(self, symbol: str):
        """Show detailed analysis window for a symbol"""
        try:
            # Create new window
            detail_window = tk.Toplevel(self.root)
            detail_window.title(f"Detailed Analysis - {symbol}")
            detail_window.geometry("800x600")
            
            # Get fresh data
            data = self.data_manager.get_multiple_timeframes(symbol)
            if '5m' not in data or data['5m'].empty:
                messagebox.showerror("Error", f"No data available for {symbol}")
                detail_window.destroy()
                return
            
            # Calculate indicators
            indicators = self.signal_generator.analyzer.calculate_all_indicators(data['5m'])
            
            # Create notebook for different views
            notebook = ttk.Notebook(detail_window)
            notebook.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Indicators tab
            indicators_frame = ttk.Frame(notebook)
            notebook.add(indicators_frame, text='Technical Indicators')
            self.create_indicators_display(indicators_frame, indicators)
            
            # Chart tab (simplified)
            chart_frame = ttk.Frame(notebook)
            notebook.add(chart_frame, text='Price Chart')
            self.create_simple_chart(chart_frame, data['5m'], symbol)
            
        except Exception as e:
            logger.error(f"Error showing detailed analysis: {e}")
            messagebox.showerror("Error", f"Error showing analysis: {e}")
    
    def create_indicators_display(self, parent, indicators: Dict):
        """Create indicators display"""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add indicators
        row = 0
        for key, value in indicators.items():
            if isinstance(value, (int, float)):
                ttk.Label(scrollable_frame, text=f"{key.replace('_', ' ').title()}:").grid(row=row, column=0, sticky='w', padx=5, pady=2)
                ttk.Label(scrollable_frame, text=f"{value:.4f}").grid(row=row, column=1, sticky='w', padx=5, pady=2)
            elif isinstance(value, bool):
                ttk.Label(scrollable_frame, text=f"{key.replace('_', ' ').title()}:").grid(row=row, column=0, sticky='w', padx=5, pady=2)
                ttk.Label(scrollable_frame, text="✅" if value else "❌").grid(row=row, column=1, sticky='w', padx=5, pady=2)
            else:
                ttk.Label(scrollable_frame, text=f"{key.replace('_', ' ').title()}:").grid(row=row, column=0, sticky='w', padx=5, pady=2)
                ttk.Label(scrollable_frame, text=str(value)).grid(row=row, column=1, sticky='w', padx=5, pady=2)
            row += 1
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_simple_chart(self, parent, df: pd.DataFrame, symbol: str):
        """Create a simple price chart"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), gridspec_kw={'height_ratios': [3, 1]})
            
            # Price chart
            ax1.plot(df.index, df['close'], label='Close Price', linewidth=1)
            ax1.set_title(f"{symbol} - 5m Chart")
            ax1.set_ylabel("Price")
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # Volume chart
            ax2.bar(df.index, df['volume'], alpha=0.7, color='blue')
            ax2.set_ylabel("Volume")
            ax2.set_xlabel("Time")
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
            
        except Exception as e:
            logger.error(f"Error creating chart: {e}")
            ttk.Label(parent, text=f"Error creating chart: {e}").pack()
    
    def run(self):
        """Start the GUI application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error running GUI: {e}")
    
    def on_closing(self):
        """Handle application closing"""
        self.stop_scanning()
        self.save_config()
        self.root.destroy()

# Risk Management Helper Functions
class RiskManager:
    @staticmethod
    def calculate_position_size(account_balance: float, risk_per_trade: float, 
                              entry_price: float, stop_loss: float) -> float:
        """Calculate position size based on risk management rules"""
        risk_amount = account_balance * (risk_per_trade / 100)
        price_diff = abs(entry_price - stop_loss)
        position_size = risk_amount / price_diff
        return position_size
    
    @staticmethod
    def validate_risk_reward(entry_price: float, stop_loss: float, take_profit: float, min_rr: float = 2.0) -> bool:
        """Validate if trade meets minimum risk/reward ratio"""
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        if risk == 0:
            return False
        rr_ratio = reward / risk
        return rr_ratio >= min_rr

# Market Scanner for Additional Opportunities
class MarketScanner:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def scan_for_volume_spikes(self, symbols: List[str], threshold: float = 3.0) -> List[Dict]:
        """Scan for unusual volume spikes across symbols"""
        volume_alerts = []
        
        for symbol in symbols:
            try:
                df = self.data_manager.get_market_data(symbol, '5m', 50)
                if len(df) < 20:
                    continue
                
                current_volume = df['volume'].iloc[-1]
                avg_volume = df['volume'].iloc[-20:-1].mean()
                
                if current_volume > (avg_volume * threshold):
                    price_change = ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
                    
                    volume_alerts.append({
                        'symbol': symbol,
                        'volume_ratio': current_volume / avg_volume,
                        'price_change': price_change,
                        'current_price': df['close'].iloc[-1],
                        'timestamp': datetime.now()
                    })
            except Exception as e:
                logger.error(f"Error scanning volume for {symbol}: {e}")
                continue
        
        return sorted(volume_alerts, key=lambda x: x['volume_ratio'], reverse=True)
    
    def scan_for_breakouts(self, symbols: List[str]) -> List[Dict]:
        """Scan for price breakouts from recent ranges"""
        breakout_alerts = []
        
        for symbol in symbols:
            try:
                df = self.data_manager.get_market_data(symbol, '15m', 100)
                if len(df) < 50:
                    continue
                
                # Calculate 20-period high/low
                high_20 = df['high'].iloc[-20:-1].max()
                low_20 = df['low'].iloc[-20:-1].min()
                current_price = df['close'].iloc[-1]
                current_volume = df['volume'].iloc[-1]
                avg_volume = df['volume'].iloc[-20:-1].mean()
                
                # Check for breakout
                if current_price > high_20 and current_volume > avg_volume * 1.5:
                    breakout_alerts.append({
                        'symbol': symbol,
                        'type': 'upward_breakout',
                        'breakout_level': high_20,
                        'current_price': current_price,
                        'volume_ratio': current_volume / avg_volume,
                        'timestamp': datetime.now()
                    })
                elif current_price < low_20 and current_volume > avg_volume * 1.5:
                    breakout_alerts.append({
                        'symbol': symbol,
                        'type': 'downward_breakout',
                        'breakout_level': low_20,
                        'current_price': current_price,
                        'volume_ratio': current_volume / avg_volume,
                        'timestamp': datetime.now()
                    })
            except Exception as e:
                logger.error(f"Error scanning breakouts for {symbol}: {e}")
                continue
        
        return breakout_alerts

# News Sentiment Integration (Placeholder)
class NewsSentimentMonitor:
    def __init__(self):
        self.last_check = datetime.now()
    
    def get_market_sentiment(self) -> Dict:
        """Get overall market sentiment (placeholder implementation)"""
        # This would integrate with news APIs like Alpha Vantage, NewsAPI, etc.
        return {
            'overall_sentiment': 0.1,  # -1 to 1 scale
            'fear_greed_index': 45,    # 0-100 scale
            'news_count': 15,
            'last_updated': datetime.now()
        }
    
    def get_symbol_sentiment(self, symbol: str) -> Dict:
        """Get sentiment for specific symbol"""
        # Placeholder - would integrate with symbol-specific news
        return {
            'sentiment_score': 0.05,
            'news_count': 3,
            'last_updated': datetime.now()
        }

# Main execution
if __name__ == "__main__":
    try:
        # Create and run the trading bot GUI
        bot = TradingBotGUI()
        bot.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Error starting application: {e}")
        input("Press Enter to exit...")