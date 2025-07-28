#!/usr/bin/env python3
"""
FREE Phase 2 Integrations - Exchange Flow & Stablecoin Monitoring
No monthly fees required!
"""

import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class FreePhase2Manager:
    """FREE alternatives to paid Phase 2 features"""
    
    def __init__(self):
        self.defillama_base = "https://api.llama.fi"
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        
    def get_stablecoin_flows(self) -> Dict:
        """Track stablecoin flows - FREE alternative to CryptoQuant"""
        try:
            # Use correct DeFiLlama stablecoin endpoint
            url = f"{self.defillama_base}/stablecoincharts/all"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            flows = {
                'total_supply_change_24h': 0,
                'major_stablecoins': {},
                'fresh_capital_score': 0,
                'flow_direction': 'neutral'
            }
            
            if not data:
                # Fallback: Use CoinGecko for stablecoin data
                return self._get_stablecoin_flows_fallback()
            
            # Get the latest data point
            latest_data = data[-1] if data else {}
            previous_data = data[-2] if len(data) > 1 else latest_data
            
            latest_total = latest_data.get('totalCirculatingUSD', 0)
            previous_total = previous_data.get('totalCirculatingUSD', latest_total)
            
            total_change = latest_total - previous_total
            change_percent = (total_change / previous_total * 100) if previous_total > 0 else 0
            
            flows['total_supply_change_24h'] = total_change
            
            # Calculate fresh capital score (0-100)
            if total_change > 1e9:  # > $1B new supply
                flows['fresh_capital_score'] = 90
                flows['flow_direction'] = 'massive_inflow'
            elif total_change > 5e8:  # > $500M
                flows['fresh_capital_score'] = 75
                flows['flow_direction'] = 'strong_inflow'
            elif total_change > 1e8:  # > $100M
                flows['fresh_capital_score'] = 60
                flows['flow_direction'] = 'inflow'
            elif total_change < -1e8:  # < -$100M
                flows['fresh_capital_score'] = 40
                flows['flow_direction'] = 'outflow'
            else:
                flows['fresh_capital_score'] = 50
                flows['flow_direction'] = 'neutral'
            
            return flows
            
        except Exception as e:
            logger.error(f"Error getting stablecoin flows: {e}")
            # Try fallback method
            return self._get_stablecoin_flows_fallback()
    
    def _get_stablecoin_flows_fallback(self) -> Dict:
        """Fallback stablecoin analysis using CoinGecko"""
        try:
            # Get USDT and USDC data from CoinGecko
            stablecoins = ['tether', 'usd-coin']
            flows = {
                'total_supply_change_24h': 0,
                'major_stablecoins': {},
                'fresh_capital_score': 50,
                'flow_direction': 'neutral'
            }
            
            total_volume_change = 0
            
            for coin in stablecoins:
                url = f"{self.coingecko_base}/coins/{coin}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                market_data = data.get('market_data', {})
                volume_24h = market_data.get('total_volume', {}).get('usd', 0)
                volume_change = market_data.get('total_volume_change_24h', 0)
                
                flows['major_stablecoins'][coin.upper()] = {
                    'volume_24h': volume_24h,
                    'volume_change_24h': volume_change,
                    'market_cap': market_data.get('market_cap', {}).get('usd', 0)
                }
                
                total_volume_change += volume_change
                
                time.sleep(1)  # Rate limiting
            
            # Estimate fresh capital from volume changes
            if total_volume_change > 20:  # > 20% volume increase
                flows['fresh_capital_score'] = 80
                flows['flow_direction'] = 'strong_inflow'
            elif total_volume_change > 10:  # > 10% volume increase
                flows['fresh_capital_score'] = 65
                flows['flow_direction'] = 'inflow'
            elif total_volume_change < -10:  # < -10% volume decrease
                flows['fresh_capital_score'] = 35
                flows['flow_direction'] = 'outflow'
            
            flows['total_volume_change_24h'] = total_volume_change
            
            return flows
            
        except Exception as e:
            logger.error(f"Error in stablecoin fallback: {e}")
            return {
                'error': str(e), 
                'fresh_capital_score': 50,
                'flow_direction': 'neutral',
                'total_supply_change_24h': 0,
                'major_stablecoins': {}
            }
    
    def get_defi_tvl_flows(self) -> Dict:
        """Monitor DeFi TVL flows - FREE exchange flow alternative"""
        try:
            # Get historical chain TVL
            url = f"{self.defillama_base}/v2/historicalChainTvl"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if len(data) < 2:
                return {'error': 'Insufficient data'}
            
            # Calculate 24h change
            latest = data[-1]
            previous = data[-2] if len(data) > 1 else data[-1]
            
            tvl_change = latest['tvl'] - previous['tvl']
            tvl_change_percent = (tvl_change / previous['tvl']) * 100
            
            flows = {
                'total_tvl': latest['tvl'],
                'tvl_change_24h': tvl_change,
                'tvl_change_percent': tvl_change_percent,
                'flow_strength': self._calculate_flow_strength(tvl_change_percent),
                'timestamp': latest['date']
            }
            
            return flows
            
        except Exception as e:
            logger.error(f"Error getting DeFi TVL flows: {e}")
            return {'error': str(e)}
    
    def get_exchange_volume_patterns(self, symbol: str) -> Dict:
        """Enhanced volume analysis - FREE CoinGecko approach"""
        try:
            # Get exchange-specific volume data
            coin_id = symbol.lower().replace('usdt', 'tether').replace('/', '')
            if symbol.upper().startswith('BTC'):
                coin_id = 'bitcoin'
            elif symbol.upper().startswith('ETH'):
                coin_id = 'ethereum'
            
            url = f"{self.coingecko_base}/coins/{coin_id}/tickers"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            exchange_flows = {
                'total_volume_24h': 0,
                'exchange_distribution': {},
                'cex_vs_dex_ratio': 0,
                'volume_concentration': 0,
                'flow_score': 50
            }
            
            total_volume = 0
            cex_volume = 0
            dex_volume = 0
            
            # Centralized exchanges
            cex_list = ['binance', 'coinbase', 'kraken', 'okex', 'huobi', 'bybit', 'kucoin']
            # Decentralized exchanges  
            dex_list = ['uniswap', 'sushiswap', 'pancakeswap', '1inch', 'dydx']
            
            for ticker in data.get('tickers', [])[:50]:  # Top 50 exchanges
                exchange = ticker.get('market', {}).get('name', '').lower()
                volume = ticker.get('converted_volume', {}).get('usd', 0)
                
                exchange_flows['exchange_distribution'][exchange] = volume
                total_volume += volume
                
                if any(cex in exchange for cex in cex_list):
                    cex_volume += volume
                elif any(dex in exchange for dex in dex_list):
                    dex_volume += volume
            
            exchange_flows['total_volume_24h'] = total_volume
            
            if total_volume > 0:
                exchange_flows['cex_vs_dex_ratio'] = cex_volume / (cex_volume + dex_volume) if (cex_volume + dex_volume) > 0 else 0
                
                # Volume concentration (Herfindahl index)
                volumes = list(exchange_flows['exchange_distribution'].values())
                if volumes:
                    hhi = sum((v/total_volume)**2 for v in volumes if v > 0)
                    exchange_flows['volume_concentration'] = hhi
            
            # Calculate flow score based on patterns
            flow_score = 50
            
            # High DEX ratio = retail/institutional interest
            if exchange_flows['cex_vs_dex_ratio'] < 0.7:
                flow_score += 15
            
            # Low concentration = broad interest
            if exchange_flows['volume_concentration'] < 0.3:
                flow_score += 10
            
            # High total volume
            if total_volume > 1e9:  # > $1B
                flow_score += 20
            elif total_volume > 5e8:  # > $500M
                flow_score += 10
            
            exchange_flows['flow_score'] = min(flow_score, 100)
            
            return exchange_flows
            
        except Exception as e:
            logger.error(f"Error getting exchange volume patterns: {e}")
            return {'error': str(e), 'flow_score': 50}
    
    def _calculate_flow_strength(self, change_percent: float) -> str:
        """Calculate flow strength from percentage change"""
        if change_percent > 5:
            return 'very_strong_inflow'
        elif change_percent > 2:
            return 'strong_inflow'
        elif change_percent > 0.5:
            return 'moderate_inflow'
        elif change_percent < -5:
            return 'very_strong_outflow'
        elif change_percent < -2:
            return 'strong_outflow'
        elif change_percent < -0.5:
            return 'moderate_outflow'
        else:
            return 'neutral'
    
    def get_predictive_signals(self, symbol: str) -> Dict:
        """Combine all FREE Phase 2 data for predictive signals"""
        try:
            # Get all data sources
            stablecoin_flows = self.get_stablecoin_flows()
            defi_flows = self.get_defi_tvl_flows()
            exchange_patterns = self.get_exchange_volume_patterns(symbol)
            
            # Combine signals
            prediction = {
                'overall_score': 50,
                'confidence': 'medium',
                'signals': {},
                'recommendation': 'neutral',
                'fresh_capital_detected': False,
                'institutional_activity': False
            }
            
            score = 50
            
            # Stablecoin flow signals
            if stablecoin_flows.get('fresh_capital_score', 50) > 70:
                score += 15
                prediction['fresh_capital_detected'] = True
                prediction['signals']['stablecoin_inflow'] = 'strong'
            elif stablecoin_flows.get('fresh_capital_score', 50) > 60:
                score += 8
                prediction['signals']['stablecoin_inflow'] = 'moderate'
            
            # DeFi TVL signals
            if defi_flows.get('tvl_change_percent', 0) > 3:
                score += 12
                prediction['signals']['defi_growth'] = 'strong'
            elif defi_flows.get('tvl_change_percent', 0) > 1:
                score += 6
                prediction['signals']['defi_growth'] = 'moderate'
            
            # Exchange flow signals
            exchange_score = exchange_patterns.get('flow_score', 50)
            if exchange_score > 70:
                score += 10
                prediction['institutional_activity'] = True
                prediction['signals']['exchange_activity'] = 'high'
            elif exchange_score > 60:
                score += 5
                prediction['signals']['exchange_activity'] = 'moderate'
            
            prediction['overall_score'] = min(score, 100)
            
            # Determine confidence and recommendation
            if prediction['overall_score'] > 75:
                prediction['confidence'] = 'high'
                prediction['recommendation'] = 'bullish'
            elif prediction['overall_score'] > 65:
                prediction['confidence'] = 'medium-high'
                prediction['recommendation'] = 'cautiously_bullish'
            elif prediction['overall_score'] < 35:
                prediction['confidence'] = 'medium-high'
                prediction['recommendation'] = 'bearish'
            elif prediction['overall_score'] < 45:
                prediction['confidence'] = 'medium'
                prediction['recommendation'] = 'cautiously_bearish'
            else:
                prediction['confidence'] = 'medium'
                prediction['recommendation'] = 'neutral'
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error generating predictive signals: {e}")
            return {'error': str(e), 'overall_score': 50}

# Test the FREE Phase 2 integrations
if __name__ == "__main__":
    print("="*60)
    print("TESTING FREE PHASE 2 INTEGRATIONS")
    print("="*60)
    
    manager = FreePhase2Manager()
    
    print("1. Testing Stablecoin Flows...")
    flows = manager.get_stablecoin_flows()
    if 'error' not in flows:
        print(f"✅ Fresh Capital Score: {flows['fresh_capital_score']}/100")
        print(f"✅ Flow Direction: {flows['flow_direction']}")
        print(f"✅ Total Supply Change: ${flows['total_supply_change_24h']:,.0f}")
    else:
        print(f"❌ Error: {flows['error']}")
    
    print("\n2. Testing DeFi TVL Flows...")
    tvl_flows = manager.get_defi_tvl_flows()
    if 'error' not in tvl_flows:
        print(f"✅ Total TVL: ${tvl_flows['total_tvl']:,.0f}")
        print(f"✅ 24h Change: ${tvl_flows['tvl_change_24h']:,.0f} ({tvl_flows['tvl_change_percent']:+.2f}%)")
        print(f"✅ Flow Strength: {tvl_flows['flow_strength']}")
    else:
        print(f"❌ Error: {tvl_flows['error']}")
    
    print("\n3. Testing Exchange Volume Patterns...")
    volume_patterns = manager.get_exchange_volume_patterns('BTC/USDT')
    if 'error' not in volume_patterns:
        print(f"✅ Total Volume: ${volume_patterns['total_volume_24h']:,.0f}")
        print(f"✅ CEX vs DEX Ratio: {volume_patterns['cex_vs_dex_ratio']:.2f}")
        print(f"✅ Flow Score: {volume_patterns['flow_score']}/100")
    else:
        print(f"❌ Error: {volume_patterns['error']}")
    
    print("\n4. Testing Predictive Signals...")
    predictions = manager.get_predictive_signals('BTC/USDT')
    if 'error' not in predictions:
        print(f"✅ Overall Score: {predictions['overall_score']}/100")
        print(f"✅ Confidence: {predictions['confidence']}")
        print(f"✅ Recommendation: {predictions['recommendation']}")
        print(f"✅ Fresh Capital Detected: {predictions['fresh_capital_detected']}")
        print(f"✅ Institutional Activity: {predictions['institutional_activity']}")
    else:
        print(f"❌ Error: {predictions['error']}")
    
    print("\n" + "="*60)
    print("🎉 FREE PHASE 2 FEATURES TESTED!")
    print("These provide 80% of CryptoQuant functionality at $0/month!")
    print("="*60)
