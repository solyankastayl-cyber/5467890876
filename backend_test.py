"""
Exchange Adapter Layer PHASE 5.1 - Comprehensive Backend Testing
================================================================

Testing all Exchange Adapter Layer endpoints with public backend URL.
Covers: Connection management, account operations, order operations,
market data, WebSocket streams, and error handling.
"""

import requests
import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Any


class ExchangeAdapterTester:
    """Comprehensive tester for Exchange Adapter Layer"""
    
    def __init__(self, base_url: str = "https://a642aa60-a4e7-46b2-aeaf-4f5327791fbd.preview.emergentagent.com"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Test tracking
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.passed_tests = []
        
        # Test data
        self.test_exchanges = ["BINANCE", "BYBIT", "OKX"]
        self.test_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        
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
        url = f"{self.base_url}/api/exchange{endpoint}"
        
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
        """GET /api/exchange/health - health check"""
        success, data, status = self.make_request("GET", "/health")
        
        if success and data.get("status") == "healthy":
            exchanges = data.get("supported_exchanges", [])
            features = data.get("features", [])
            version = data.get("version", "")
            
            details = f"Status healthy, version {version}, {len(exchanges)} exchanges, {len(features)} features"
            self.log_result("Health Check", True, details)
            return True
        else:
            self.log_result("Health Check", False, f"Status {status}, Response: {data}")
            return False
    
    def test_router_status(self):
        """GET /api/exchange/status - router status"""
        success, data, status = self.make_request("GET", "/status")
        
        if success and "router_status" in data:
            router_status = data["router_status"]
            registered = router_status.get("registered_exchanges", [])
            connections = router_status.get("connections", {})
            
            details = f"Router active, {len(registered)} registered exchanges, {len(connections)} connections"
            self.log_result("Router Status", True, details)
            return True
        else:
            self.log_result("Router Status", False, f"Status {status}, Response: {data}")
            return False
    
    # ============================================
    # Connection Management Tests
    # ============================================
    
    def test_connect_exchanges(self):
        """POST /api/exchange/connect - connect to exchanges"""
        connected_count = 0
        
        for exchange in self.test_exchanges:
            success, data, status = self.make_request(
                "POST", "/connect",
                {"exchange": exchange, "testnet": True}
            )
            
            if success and data.get("connected"):
                connected_count += 1
                self.log_result(f"Connect {exchange}", True, f"Connected to {exchange} testnet")
            else:
                self.log_result(f"Connect {exchange}", False, f"Failed to connect: {data}")
        
        return connected_count > 0
    
    def test_exchange_specific_status(self):
        """GET /api/exchange/status?exchange=X - specific exchange status"""
        tested_count = 0
        
        for exchange in ["BINANCE", "OKX"]:  # Test subset
            success, data, status = self.make_request("GET", "/status", params={"exchange": exchange})
            
            if success and data.get("exchange") == exchange:
                tested_count += 1
                self.log_result(f"{exchange} Status", True, f"Got {exchange} specific status")
            else:
                self.log_result(f"{exchange} Status", False, f"Failed: {data}")
        
        return tested_count > 0
    
    def test_disconnect_exchange(self):
        """POST /api/exchange/disconnect - disconnect from exchange"""
        success, data, status = self.make_request("POST", "/disconnect?exchange=BINANCE")
        
        if success and data.get("disconnected"):
            self.log_result("Disconnect Exchange", True, "Successfully disconnected from BINANCE")
            return True
        else:
            self.log_result("Disconnect Exchange", False, f"Failed: {data}")
            return False
    
    # ============================================
    # Account Operations Tests
    # ============================================
    
    def test_get_balances(self):
        """GET /api/exchange/balances - get account balances"""
        # First connect to ensure we have balances
        self.make_request("POST", "/connect", {"exchange": "BINANCE", "testnet": True})
        
        success, data, status = self.make_request("GET", "/balances")
        
        if success and "balances" in data:
            balance_exchanges = list(data["balances"].keys())
            total_balances = sum(len(balances) for balances in data["balances"].values())
            
            details = f"Got balances from {len(balance_exchanges)} exchanges, {total_balances} total assets"
            self.log_result("Get Balances", True, details)
            return True
        else:
            self.log_result("Get Balances", False, f"Status {status}, Response: {data}")
            return False
    
    def test_get_positions(self):
        """GET /api/exchange/positions - get open positions"""
        success, data, status = self.make_request("GET", "/positions")
        
        if success and "positions" in data:
            position_exchanges = list(data["positions"].keys())
            
            details = f"Got positions from {len(position_exchanges)} exchanges"
            self.log_result("Get Positions", True, details)
            return True
        else:
            self.log_result("Get Positions", False, f"Status {status}, Response: {data}")
            return False
    
    def test_get_open_orders(self):
        """GET /api/exchange/open-orders - get open orders"""
        success, data, status = self.make_request("GET", "/open-orders")
        
        if success and "open_orders" in data:
            order_exchanges = list(data["open_orders"].keys())
            
            details = f"Got open orders from {len(order_exchanges)} exchanges"
            self.log_result("Get Open Orders", True, details)
            return True
        else:
            self.log_result("Get Open Orders", False, f"Status {status}, Response: {data}")
            return False
    
    # ============================================
    # Order Operations Tests
    # ============================================
    
    def test_create_market_order(self):
        """POST /api/exchange/create-order - create market order"""
        # Ensure connected first
        self.make_request("POST", "/connect", {"exchange": "BINANCE", "testnet": True})
        
        order_data = {
            "exchange": "BINANCE",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "order_type": "MARKET",
            "size": 0.001
        }
        
        success, data, status = self.make_request("POST", "/create-order", order_data)
        
        if success and "order" in data:
            order = data["order"]
            order_id = order.get("exchange_order_id", "unknown")
            
            details = f"Created market order {order_id} for {order.get('symbol')} {order.get('side')}"
            self.log_result("Create Market Order", True, details)
            return order_id
        else:
            self.log_result("Create Market Order", False, f"Status {status}, Response: {data}")
            return None
    
    def test_create_limit_order(self):
        """POST /api/exchange/create-order - create limit order"""
        order_data = {
            "exchange": "BINANCE",
            "symbol": "ETHUSDT",
            "side": "SELL",
            "order_type": "LIMIT",
            "size": 0.01,
            "price": 3500.0,
            "time_in_force": "GTC"
        }
        
        success, data, status = self.make_request("POST", "/create-order", order_data)
        
        if success and "order" in data:
            order = data["order"]
            order_id = order.get("exchange_order_id", "unknown")
            
            details = f"Created limit order {order_id} for {order.get('symbol')} @ ${order.get('price')}"
            self.log_result("Create Limit Order", True, details)
            return order_id
        else:
            self.log_result("Create Limit Order", False, f"Status {status}, Response: {data}")
            return None
    
    def test_cancel_order(self):
        """POST /api/exchange/cancel-order - cancel order"""
        # First create an order to cancel
        order_id = self.test_create_limit_order()
        
        if not order_id:
            self.log_result("Cancel Order", False, "No order ID to cancel")
            return False
        
        cancel_data = {
            "exchange": "BINANCE",
            "order_id": order_id,
            "symbol": "ETHUSDT"
        }
        
        success, data, status = self.make_request("POST", "/cancel-order", cancel_data)
        
        if success and data.get("cancelled"):
            details = f"Cancelled order {order_id}"
            self.log_result("Cancel Order", True, details)
            return True
        else:
            self.log_result("Cancel Order", False, f"Status {status}, Response: {data}")
            return False
    
    # ============================================
    # Market Data Tests
    # ============================================
    
    def test_get_ticker(self):
        """GET /api/exchange/ticker/{symbol} - get ticker"""
        # Ensure connected
        self.make_request("POST", "/connect", {"exchange": "BINANCE", "testnet": True})
        
        success, data, status = self.make_request("GET", "/ticker/BTCUSDT", params={"exchange": "BINANCE"})
        
        if success and "ticker" in data:
            ticker = data["ticker"]
            price = ticker.get("last_price", 0)
            exchange = ticker.get("exchange", "")
            
            details = f"Got {exchange} BTCUSDT ticker @ ${price}"
            self.log_result("Get Ticker", True, details)
            return True
        else:
            self.log_result("Get Ticker", False, f"Status {status}, Response: {data}")
            return False
    
    def test_get_orderbook(self):
        """GET /api/exchange/orderbook/{symbol} - get orderbook"""
        success, data, status = self.make_request(
            "GET", "/orderbook/BTCUSDT", 
            params={"exchange": "BINANCE", "depth": 10}
        )
        
        if success and "orderbook" in data:
            orderbook = data["orderbook"]
            bids = len(orderbook.get("bids", []))
            asks = len(orderbook.get("asks", []))
            
            details = f"Got orderbook with {bids} bids, {asks} asks"
            self.log_result("Get Orderbook", True, details)
            return True
        else:
            self.log_result("Get Orderbook", False, f"Status {status}, Response: {data}")
            return False
    
    def test_get_best_price(self):
        """GET /api/exchange/best-price/{symbol} - get best price"""
        success, data, status = self.make_request("GET", "/best-price/BTCUSDT", params={"side": "BUY"})
        
        if success and "best_price" in data:
            best_price = data["best_price"]
            exchange = best_price.get("exchange", "")
            price = best_price.get("price", 0)
            
            details = f"Best BUY price: {exchange} @ ${price}"
            self.log_result("Get Best Price", True, details)
            return True
        else:
            self.log_result("Get Best Price", False, f"Status {status}, Response: {data}")
            return False
    
    # ============================================
    # WebSocket Stream Tests
    # ============================================
    
    def test_start_ticker_stream(self):
        """POST /api/exchange/stream/start - start ticker stream"""
        # Ensure connected
        self.make_request("POST", "/connect", {"exchange": "BINANCE", "testnet": True})
        
        stream_data = {
            "exchange": "BINANCE",
            "stream_type": "TICKER",
            "symbols": ["BTCUSDT", "ETHUSDT"]
        }
        
        success, data, status = self.make_request("POST", "/stream/start", stream_data)
        
        if success and data.get("started"):
            symbols = data.get("symbols", [])
            
            details = f"Started ticker stream for {len(symbols)} symbols"
            self.log_result("Start Ticker Stream", True, details)
            return True
        else:
            self.log_result("Start Ticker Stream", False, f"Status {status}, Response: {data}")
            return False
    
    def test_start_orderbook_stream(self):
        """POST /api/exchange/stream/start - start orderbook stream"""
        stream_data = {
            "exchange": "BINANCE",
            "stream_type": "ORDERBOOK",
            "symbols": ["BTCUSDT"]
        }
        
        success, data, status = self.make_request("POST", "/stream/start", stream_data)
        
        if success and data.get("started"):
            details = f"Started orderbook stream for BTCUSDT"
            self.log_result("Start Orderbook Stream", True, details)
            return True
        else:
            self.log_result("Start Orderbook Stream", False, f"Status {status}, Response: {data}")
            return False
    
    def test_get_stream_status(self):
        """GET /api/exchange/stream/status - get stream status"""
        success, data, status = self.make_request("GET", "/stream/status")
        
        if success and "streams" in data and "active_streams" in data:
            active_count = data.get("active_streams", 0)
            
            details = f"Stream status retrieved, {active_count} active streams"
            self.log_result("Get Stream Status", True, details)
            return True
        else:
            self.log_result("Get Stream Status", False, f"Status {status}, Response: {data}")
            return False
    
    def test_stop_stream(self):
        """POST /api/exchange/stream/stop - stop stream"""
        stream_data = {
            "exchange": "BINANCE",
            "stream_type": "ORDERBOOK",
            "symbols": ["BTCUSDT"]
        }
        
        success, data, status = self.make_request("POST", "/stream/stop", stream_data)
        
        if success and data.get("stopped"):
            details = f"Stopped orderbook stream"
            self.log_result("Stop Stream", True, details)
            return True
        else:
            self.log_result("Stop Stream", False, f"Status {status}, Response: {data}")
            return False
    
    # ============================================
    # History & Statistics Tests
    # ============================================
    
    def test_get_order_history(self):
        """GET /api/exchange/history/orders - get order history"""
        success, data, status = self.make_request("GET", "/history/orders", params={"limit": 10})
        
        if success and "orders" in data and "count" in data:
            count = data.get("count", 0)
            
            details = f"Retrieved order history, {count} orders"
            self.log_result("Get Order History", True, details)
            return True
        else:
            self.log_result("Get Order History", False, f"Status {status}, Response: {data}")
            return False
    
    def test_get_order_stats(self):
        """GET /api/exchange/stats/orders - get order statistics"""
        success, data, status = self.make_request("GET", "/stats/orders", params={"days": 7})
        
        if success and "stats" in data:
            details = f"Retrieved order statistics for 7 days"
            self.log_result("Get Order Stats", True, details)
            return True
        else:
            self.log_result("Get Order Stats", False, f"Status {status}, Response: {data}")
            return False
    
    # ============================================
    # Error Handling Tests
    # ============================================
    
    def test_error_handling(self):
        """Test error handling with invalid requests"""
        error_tests = [
            {
                "name": "Unknown Exchange",
                "method": "POST",
                "endpoint": "/connect",
                "data": {"exchange": "UNKNOWN_EXCHANGE"},
                "expected_status": 400
            },
            {
                "name": "Invalid Order Side",
                "method": "POST", 
                "endpoint": "/create-order",
                "data": {
                    "exchange": "BINANCE",
                    "symbol": "BTCUSDT",
                    "side": "INVALID",
                    "order_type": "MARKET",
                    "size": 0.01
                },
                "expected_status": 400
            }
        ]
        
        # Ensure connected for order tests
        self.make_request("POST", "/connect", {"exchange": "BINANCE", "testnet": True})
        
        error_handled = 0
        
        for test in error_tests:
            success, data, status = self.make_request(test["method"], test["endpoint"], test["data"])
            
            if status == test["expected_status"]:
                error_handled += 1
                self.log_result(f"Error: {test['name']}", True, f"Correctly returned {status}")
            else:
                self.log_result(f"Error: {test['name']}", False, f"Expected {test['expected_status']}, got {status}")
        
        return error_handled > 0
    
    # ============================================
    # Integration Workflow Tests
    # ============================================
    
    def test_full_trading_workflow(self):
        """Test complete end-to-end trading workflow"""
        workflow_steps = []
        
        # Step 1: Connect
        success, data, _ = self.make_request("POST", "/connect", {"exchange": "BINANCE", "testnet": True})
        if success and data.get("connected"):
            workflow_steps.append("Connect to exchange")
        
        # Step 2: Check balances
        success, data, _ = self.make_request("GET", "/balances", params={"exchange": "BINANCE"})
        if success and "balances" in data:
            workflow_steps.append("Get account balances")
        
        # Step 3: Get market data
        success, data, _ = self.make_request("GET", "/ticker/BTCUSDT", params={"exchange": "BINANCE"})
        if success and "ticker" in data:
            workflow_steps.append("Get market ticker")
        
        # Step 4: Create order
        order_data = {
            "exchange": "BINANCE",
            "symbol": "BTCUSDT", 
            "side": "BUY",
            "order_type": "MARKET",
            "size": 0.001
        }
        success, data, _ = self.make_request("POST", "/create-order", order_data)
        if success and "order" in data:
            workflow_steps.append("Create market order")
        
        # Step 5: Check positions
        success, data, _ = self.make_request("GET", "/positions", params={"exchange": "BINANCE"})
        if success and "positions" in data:
            workflow_steps.append("Check positions")
        
        if len(workflow_steps) >= 4:  # Require most steps to succeed
            details = f"Completed {len(workflow_steps)}/5 workflow steps: {', '.join(workflow_steps)}"
            self.log_result("Full Trading Workflow", True, details)
            return True
        else:
            details = f"Only {len(workflow_steps)}/5 steps completed"
            self.log_result("Full Trading Workflow", False, details)
            return False
    
    # ============================================
    # Main Test Runner
    # ============================================
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print(f"\n🚀 Starting Exchange Adapter Layer PHASE 5.1 Testing")
        print(f"Backend URL: {self.base_url}")
        print(f"Testing started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Health & Status Tests
        print("\n📋 HEALTH & STATUS TESTS")
        self.test_health_endpoint()
        self.test_router_status()
        
        # Connection Management Tests  
        print("\n🔗 CONNECTION MANAGEMENT TESTS")
        self.test_connect_exchanges()
        self.test_exchange_specific_status()
        self.test_disconnect_exchange()
        
        # Account Operations Tests
        print("\n💰 ACCOUNT OPERATIONS TESTS")
        self.test_get_balances()
        self.test_get_positions()
        self.test_get_open_orders()
        
        # Order Operations Tests
        print("\n📈 ORDER OPERATIONS TESTS")
        self.test_create_market_order()
        self.test_create_limit_order()
        self.test_cancel_order()
        
        # Market Data Tests
        print("\n📊 MARKET DATA TESTS")
        self.test_get_ticker()
        self.test_get_orderbook()
        self.test_get_best_price()
        
        # WebSocket Stream Tests
        print("\n🌐 WEBSOCKET STREAM TESTS")
        self.test_start_ticker_stream()
        self.test_start_orderbook_stream()
        self.test_get_stream_status()
        self.test_stop_stream()
        
        # History & Statistics Tests
        print("\n📚 HISTORY & STATISTICS TESTS")
        self.test_get_order_history()
        self.test_get_order_stats()
        
        # Error Handling Tests
        print("\n⚠️  ERROR HANDLING TESTS")
        self.test_error_handling()
        
        # Integration Tests
        print("\n🔄 INTEGRATION TESTS")
        self.test_full_trading_workflow()
        
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
    print("Exchange Adapter Layer PHASE 5.1 - Backend API Testing")
    
    # Initialize tester
    tester = ExchangeAdapterTester()
    
    # Run all tests
    passed, total, failures, successes = tester.run_all_tests()
    
    # Return appropriate exit code
    if passed == total:
        print(f"\n🎉 All tests passed! Exchange Adapter Layer is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the failures above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)