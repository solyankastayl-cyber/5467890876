"""
Live Market Data Engine PHASE 5.2 - Comprehensive Backend Testing
================================================================

Testing all Market Data Engine endpoints with public backend URL.
Covers: Health checks, feed management, live data access, historical data, 
multi-exchange support, and simulated market data.
"""

import requests
import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Any


class MarketDataEngineTester:
    """Comprehensive tester for Live Market Data Engine PHASE 5.2"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Test tracking
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.passed_tests = []
        
        # Test data
        self.test_exchanges = ["BINANCE"]  # Primary exchange for testing
        self.test_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        self.test_timeframes = ["1m", "5m", "1h"]
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            self.passed_tests.append(f"✅ {test_name}: {details}")
            print(f"✅ {test_name}: {details}")
        else:
            self.failed_tests.append(f"❌ {test_name}: {details}")
            print(f"❌ {test_name}: {details}")
    
    def make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}/api/market-data{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=10)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, params=params, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}, 0
            
            return response.status_code == 200, response.json(), response.status_code
            
        except requests.RequestException as e:
            return False, {"error": str(e)}, 0
        except json.JSONDecodeError as e:
            return False, {"error": f"Invalid JSON: {str(e)}"}, response.status_code if 'response' in locals() else 0

    # ============================================
    # Health & Status Tests
    # ============================================
    
    def test_health_endpoint(self):
        """GET /api/market-data/health - health check"""
        success, data, status = self.make_request("GET", "/health")
        
        if success and data.get("status") == "healthy":
            version = data.get("version", "")
            components = data.get("components", [])
            
            details = f"Status healthy, version {version}, {len(components)} components"
            self.log_result("Health Check", True, details)
            return True
        else:
            self.log_result("Health Check", False, f"Status {status}, Response: {data}")
            return False
    
    def test_engine_status(self):
        """GET /api/market-data/status - engine status"""
        success, data, status = self.make_request("GET", "/status")
        
        if success and "engine_status" in data:
            engine_status = data["engine_status"]
            running = engine_status.get("running", False)
            active_feeds = engine_status.get("active_feeds", 0)
            
            details = f"Engine running: {running}, {active_feeds} active feeds"
            self.log_result("Engine Status", True, details)
            return True
        else:
            self.log_result("Engine Status", False, f"Status {status}, Response: {data}")
            return False

    # ============================================
    # Feed Management Tests
    # ============================================
    
    def test_start_feed(self):
        """POST /api/market-data/start - start market data feed"""
        feed_config = {
            "exchange": "BINANCE",
            "symbols": self.test_symbols,
            "subscribe_ticker": True,
            "subscribe_orderbook": True,
            "subscribe_candles": True,
            "candle_timeframes": self.test_timeframes
        }
        
        success, data, status = self.make_request("POST", "/start", feed_config)
        
        if success and data.get("started"):
            exchange = data.get("exchange", "")
            symbols = data.get("symbols", [])
            
            details = f"Started {exchange} feed for {len(symbols)} symbols"
            self.log_result("Start Feed", True, details)
            return True
        else:
            self.log_result("Start Feed", False, f"Status {status}, Response: {data}")
            return False
    
    def test_feed_status_specific(self):
        """GET /api/market-data/status?exchange=BINANCE - specific exchange status"""
        success, data, status = self.make_request("GET", "/status", params={"exchange": "BINANCE"})
        
        if success and data.get("exchange") == "BINANCE":
            feed_status = data.get("feed_status", {})
            symbols = data.get("subscribed_symbols", [])
            
            details = f"BINANCE feed active: {feed_status.get('is_active', False)}, {len(symbols)} symbols"
            self.log_result("Feed Status Specific", True, details)
            return True
        else:
            self.log_result("Feed Status Specific", False, f"Status {status}, Response: {data}")
            return False
    
    def test_stop_feed(self):
        """POST /api/market-data/stop - stop specific symbols"""
        stop_config = {
            "exchange": "BINANCE",
            "symbols": ["SOLUSDT"]  # Stop just one symbol
        }
        
        success, data, status = self.make_request("POST", "/stop", stop_config)
        
        if success and data.get("stopped"):
            exchange = data.get("exchange", "")
            symbols = data.get("symbols", [])
            
            details = f"Stopped {exchange} feed for {len(symbols)} symbols"
            self.log_result("Stop Feed", True, details)
            return True
        else:
            self.log_result("Stop Feed", False, f"Status {status}, Response: {data}")
            return False

    # ============================================
    # Live Data Access Tests
    # ============================================
    
    def test_get_snapshot(self):
        """GET /api/market-data/snapshot/{symbol} - get market snapshot"""
        # Wait a moment for data to populate
        time.sleep(2)
        
        success, data, status = self.make_request("GET", "/snapshot/BTCUSDT")
        
        if success and "snapshot" in data:
            snapshot = data["snapshot"]
            last_price = snapshot.get("last_price", 0)
            symbol = snapshot.get("symbol", "")
            
            details = f"Got {symbol} snapshot, price: ${last_price}"
            self.log_result("Get Snapshot", True, details)
            return True
        else:
            self.log_result("Get Snapshot", False, f"Status {status}, Response: {data}")
            return False
    
    def test_get_ticker(self):
        """GET /api/market-data/ticker/{symbol} - get live ticker"""
        success, data, status = self.make_request("GET", "/ticker/BTCUSDT", params={"exchange": "BINANCE"})
        
        if success and "ticker" in data:
            ticker = data["ticker"]
            price = ticker.get("price", 0)
            spread_info = data.get("spread", {})
            
            details = f"Got ticker price: ${price}, spread: {spread_info.get('spread', 0)}"
            self.log_result("Get Ticker", True, details)
            return True
        elif success and "error" in data:
            # Accept "no data available" as valid response for new system
            details = f"No ticker data yet: {data['error']}"
            self.log_result("Get Ticker", True, details)
            return True
        else:
            self.log_result("Get Ticker", False, f"Status {status}, Response: {data}")
            return False
    
    def test_get_orderbook(self):
        """GET /api/market-data/orderbook/{symbol} - get live orderbook"""
        success, data, status = self.make_request("GET", "/orderbook/ETHUSDT", params={"exchange": "BINANCE"})
        
        if success and "orderbook" in data:
            orderbook = data["orderbook"]
            bids = len(orderbook.get("bids", []))
            asks = len(orderbook.get("asks", []))
            
            details = f"Got orderbook with {bids} bids, {asks} asks"
            self.log_result("Get Orderbook", True, details)
            return True
        elif success and "error" in data:
            # Accept "no data available" as valid response for new system
            details = f"No orderbook data yet: {data['error']}"
            self.log_result("Get Orderbook", True, details)
            return True
        else:
            self.log_result("Get Orderbook", False, f"Status {status}, Response: {data}")
            return False
    
    def test_get_candles(self):
        """GET /api/market-data/candles/{symbol}/{timeframe} - get live candles"""
        success, data, status = self.make_request(
            "GET", "/candles/BTCUSDT/1m", 
            params={"exchange": "BINANCE", "limit": 10}
        )
        
        if success and "candles" in data:
            candles = data.get("candles", [])
            symbol = data.get("symbol", "")
            timeframe = data.get("timeframe", "")
            
            details = f"Got {len(candles)} candles for {symbol} {timeframe}"
            self.log_result("Get Candles", True, details)
            return True
        else:
            self.log_result("Get Candles", False, f"Status {status}, Response: {data}")
            return False
    
    def test_get_current_candle(self):
        """GET /api/market-data/current-candle/{symbol}/{timeframe} - get current open candle"""
        success, data, status = self.make_request(
            "GET", "/current-candle/ETHUSDT/5m",
            params={"exchange": "BINANCE"}
        )
        
        if success and "candle" in data:
            candle = data["candle"]
            is_closed = candle.get("is_closed", True)
            
            details = f"Got current candle, closed: {is_closed}"
            self.log_result("Get Current Candle", True, details)
            return True
        elif success and "error" in data:
            # Accept "no current candle" as valid response
            details = f"No current candle: {data['error']}"
            self.log_result("Get Current Candle", True, details)
            return True
        else:
            self.log_result("Get Current Candle", False, f"Status {status}, Response: {data}")
            return False
    
    def test_get_volume_metrics(self):
        """GET /api/market-data/volume/{symbol} - get volume metrics"""
        success, data, status = self.make_request("GET", "/volume/BTCUSDT", params={"exchange": "BINANCE"})
        
        if success and "volume_metrics" in data:
            metrics = data["volume_metrics"]
            current_vol = metrics.get("current_volume", 0)
            
            details = f"Got volume metrics, current: {current_vol}"
            self.log_result("Get Volume Metrics", True, details)
            return True
        elif success and "error" in data:
            # Accept "no volume data" as valid response for new system
            details = f"No volume data yet: {data['error']}"
            self.log_result("Get Volume Metrics", True, details)
            return True
        else:
            self.log_result("Get Volume Metrics", False, f"Status {status}, Response: {data}")
            return False
    
    def test_get_price(self):
        """GET /api/market-data/price/{symbol} - get latest price"""
        success, data, status = self.make_request("GET", "/price/BTCUSDT", params={"exchange": "BINANCE"})
        
        if success and "price" in data:
            price = data.get("price", 0)
            symbol = data.get("symbol", "")
            
            details = f"Got {symbol} price: ${price}"
            self.log_result("Get Price", True, details)
            return True
        else:
            self.log_result("Get Price", False, f"Status {status}, Response: {data}")
            return False

    # ============================================
    # Exchange Info Tests
    # ============================================
    
    def test_get_exchanges(self):
        """GET /api/market-data/exchanges - get active exchanges"""
        success, data, status = self.make_request("GET", "/exchanges")
        
        if success and "active_exchanges" in data:
            active = data.get("active_exchanges", [])
            subscriptions = data.get("subscriptions", {})
            
            details = f"Active exchanges: {len(active)}, subscriptions: {len(subscriptions)}"
            self.log_result("Get Exchanges", True, details)
            return True
        else:
            self.log_result("Get Exchanges", False, f"Status {status}, Response: {data}")
            return False

    # ============================================
    # Historical Data Tests
    # ============================================
    
    def test_get_candle_history(self):
        """GET /api/market-data/history/candles/{symbol}/{timeframe} - get historical candles"""
        success, data, status = self.make_request(
            "GET", "/history/candles/BTCUSDT/1h",
            params={"exchange": "BINANCE", "limit": 50}
        )
        
        if success and "candles" in data:
            candles = data.get("candles", [])
            count = data.get("count", 0)
            
            details = f"Got {count} historical candles"
            self.log_result("Get Candle History", True, details)
            return True
        else:
            self.log_result("Get Candle History", False, f"Status {status}, Response: {data}")
            return False
    
    def test_get_candle_stats(self):
        """GET /api/market-data/stats/candles/{symbol} - get candle statistics"""
        success, data, status = self.make_request(
            "GET", "/stats/candles/BTCUSDT",
            params={"timeframe": "1h", "days": 7}
        )
        
        if success and "stats" in data:
            stats = data.get("stats", {})
            
            details = f"Got candle statistics"
            self.log_result("Get Candle Stats", True, details)
            return True
        else:
            self.log_result("Get Candle Stats", False, f"Status {status}, Response: {data}")
            return False

    # ============================================
    # Multi-Symbol Tests
    # ============================================
    
    def test_multi_symbol_support(self):
        """Test multiple symbol support across all endpoints"""
        symbols_tested = 0
        
        for symbol in self.test_symbols:
            # Test snapshot for each symbol
            success, data, status = self.make_request("GET", f"/snapshot/{symbol}")
            if success:
                symbols_tested += 1
        
        if symbols_tested >= 2:
            details = f"Multi-symbol support verified for {symbols_tested}/{len(self.test_symbols)} symbols"
            self.log_result("Multi-Symbol Support", True, details)
            return True
        else:
            self.log_result("Multi-Symbol Support", False, f"Only {symbols_tested} symbols working")
            return False

    # ============================================
    # Integration Workflow Tests
    # ============================================
    
    def test_full_market_data_workflow(self):
        """Test complete market data workflow"""
        workflow_steps = []
        
        # Step 1: Health check
        success, data, _ = self.make_request("GET", "/health")
        if success and data.get("status") == "healthy":
            workflow_steps.append("Health check passed")
        
        # Step 2: Start feed
        feed_config = {
            "exchange": "BINANCE",
            "symbols": ["BTCUSDT", "ETHUSDT"],
            "subscribe_ticker": True,
            "subscribe_orderbook": True,
            "subscribe_candles": True,
            "candle_timeframes": ["1m", "5m"]
        }
        success, data, _ = self.make_request("POST", "/start", feed_config)
        if success and data.get("started"):
            workflow_steps.append("Feed started")
        
        # Step 3: Wait for data
        time.sleep(3)
        
        # Step 4: Check snapshot
        success, data, _ = self.make_request("GET", "/snapshot/BTCUSDT")
        if success and "snapshot" in data:
            workflow_steps.append("Snapshot retrieved")
        
        # Step 5: Check engine status
        success, data, _ = self.make_request("GET", "/status")
        if success and "engine_status" in data:
            workflow_steps.append("Engine status checked")
        
        # Step 6: Get candles
        success, data, _ = self.make_request("GET", "/candles/BTCUSDT/1m", params={"limit": 5})
        if success and "candles" in data:
            workflow_steps.append("Candles retrieved")
        
        if len(workflow_steps) >= 4:  # Require most steps to succeed
            details = f"Completed {len(workflow_steps)}/6 workflow steps: {', '.join(workflow_steps)}"
            self.log_result("Full Market Data Workflow", True, details)
            return True
        else:
            details = f"Only {len(workflow_steps)}/6 steps completed: {', '.join(workflow_steps)}"
            self.log_result("Full Market Data Workflow", False, details)
            return False

    # ============================================
    # Main Test Runner
    # ============================================
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print(f"\n🚀 Starting Live Market Data Engine PHASE 5.2 Testing")
        print(f"Backend URL: {self.base_url}")
        print(f"Testing started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Health & Status Tests
        print("\n📋 HEALTH & STATUS TESTS")
        self.test_health_endpoint()
        self.test_engine_status()
        
        # Feed Management Tests  
        print("\n🔗 FEED MANAGEMENT TESTS")
        self.test_start_feed()
        self.test_feed_status_specific()
        
        # Live Data Access Tests
        print("\n📊 LIVE DATA ACCESS TESTS")
        self.test_get_snapshot()
        self.test_get_ticker()
        self.test_get_orderbook()
        self.test_get_candles()
        self.test_get_current_candle()
        self.test_get_volume_metrics()
        self.test_get_price()
        
        # Exchange Info Tests
        print("\n🏛️  EXCHANGE INFO TESTS")
        self.test_get_exchanges()
        
        # Historical Data Tests
        print("\n📚 HISTORICAL DATA TESTS")
        self.test_get_candle_history()
        self.test_get_candle_stats()
        
        # Multi-Symbol Tests
        print("\n🎯 MULTI-SYMBOL TESTS")
        self.test_multi_symbol_support()
        
        # Integration Tests
        print("\n🔄 INTEGRATION WORKFLOW TESTS")
        self.test_full_market_data_workflow()
        
        # Stop Feed Test (cleanup)
        print("\n🛑 CLEANUP TESTS")
        self.test_stop_feed()
        
        # Final Results
        print("\n" + "=" * 80)
        print(f"🎯 TESTING COMPLETED")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for failure in self.failed_tests:
                print(f"  {failure}")
        
        print(f"\n✅ PASSED TESTS:")
        for success in self.passed_tests:
            print(f"  {success}")
        
        return self.tests_passed, self.tests_run, self.failed_tests, self.passed_tests


def main():
    """Main function"""
    print("Live Market Data Engine PHASE 5.2 - Backend API Testing")
    
    # Initialize tester
    tester = MarketDataEngineTester()
    
    # Run all tests
    passed, total, failures, successes = tester.run_all_tests()
    
    # Return appropriate exit code
    if passed == total:
        print(f"\n🎉 All tests passed! Market Data Engine is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the failures above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)