#!/usr/bin/env python3
"""
Test vnstock API usage
"""
import asyncio
import os
from datetime import datetime, timedelta

async def test_vnstock_api():
    """Test vnstock API methods"""
    print("🔍 Testing vnstock API...")
    
    try:
        from vnstock import Vnstock
        
        # Test different approaches
        print("\n📊 Testing VNINDEX symbol...")
        
        # Method 1: Direct VNINDEX
        try:
            vnindex = Vnstock().stock(symbol="VNINDEX")
            print("  ✅ VNINDEX symbol created")
            
            # Check available methods
            print(f"  📋 Quote methods: {[method for method in dir(vnindex.quote) if not method.startswith('_')]}")
            
            # Try different methods
            methods_to_try = ['live', 'realtime', 'current', 'price', 'quote']
            
            for method in methods_to_try:
                if hasattr(vnindex.quote, method):
                    try:
                        print(f"  🔍 Trying quote.{method}()...")
                        result = getattr(vnindex.quote, method)()
                        print(f"  ✅ {method}() returned: {type(result)}")
                        if hasattr(result, 'shape'):
                            print(f"  📊 Shape: {result.shape}")
                        if hasattr(result, 'columns'):
                            print(f"  📋 Columns: {list(result.columns)}")
                        if hasattr(result, 'head'):
                            print(f"  📊 Data:\n{result.head()}")
                    except Exception as e:
                        print(f"  ❌ {method}() error: {e}")
            
        except Exception as e:
            print(f"  ❌ VNINDEX error: {e}")
        
        # Method 2: Try different symbols
        print("\n📊 Testing different symbols...")
        symbols = ["VNINDEX", "VN-INDEX", "VNINDEX.VN", "VNINDEX.VN"]
        
        for symbol in symbols:
            try:
                print(f"  🔍 Trying symbol: {symbol}")
                vnindex = Vnstock().stock(symbol=symbol)
                print(f"  ✅ {symbol} created successfully")
                
                # Try to get data
                if hasattr(vnindex.quote, 'realtime'):
                    try:
                        data = vnindex.quote.realtime()
                        print(f"  📊 Realtime data: {data}")
                    except Exception as e:
                        print(f"  ❌ Realtime error: {e}")
                        
            except Exception as e:
                print(f"  ❌ {symbol} error: {e}")
        
        # Method 3: Try market data
        print("\n📊 Testing market data...")
        try:
            market = Vnstock().market()
            print(f"  📋 Market methods: {[method for method in dir(market) if not method.startswith('_')]}")
            
            if hasattr(market, 'index_quote'):
                try:
                    index_data = market.index_quote()
                    print(f"  📊 Index data: {index_data}")
                except Exception as e:
                    print(f"  ❌ Index quote error: {e}")
                    
        except Exception as e:
            print(f"  ❌ Market error: {e}")
            
    except Exception as e:
        print(f"❌ Error importing vnstock: {e}")

async def main():
    """Run test"""
    print("🚀 Testing vnstock API...")
    print("=" * 60)
    
    await test_vnstock_api()

if __name__ == "__main__":
    asyncio.run(main())
