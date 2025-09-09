#!/usr/bin/env python3
"""
Test VN-Index data retrieval
"""
import asyncio
import os
from datetime import datetime, timedelta

async def test_vnindex_data():
    """Test getting real VN-Index data"""
    print("🔍 Testing VN-Index Data Retrieval...")
    
    try:
        from vnstock import Vnstock
        
        # Try different sources
        sources = ["VCI", "TCBS", "MSN"]
        
        for source in sources:
            print(f"\n📊 Trying source: {source}")
            try:
                vnindex = Vnstock().stock(symbol="VNINDEX", source=source)
                
                # Get historical data to get latest price
                print("  🔍 Getting historical data...")
                today = datetime.now().date()
                start_date = (today - timedelta(days=5)).strftime("%Y-%m-%d")
                end_date = today.strftime("%Y-%m-%d")
                
                hist_data = vnindex.quote.history(
                    start=start_date,
                    end=end_date,
                    interval="1D"
                )
                
                if hist_data is not None and not hist_data.empty:
                    print(f"  ✅ Historical data shape: {hist_data.shape}")
                    print(f"  📋 Historical columns: {list(hist_data.columns)}")
                    print(f"  📊 Latest data:\n{hist_data.tail()}")
                    
                    # Get latest data (most recent)
                    latest_data = hist_data.iloc[-1]
                    current_price = float(latest_data["close"])
                    volume = float(latest_data["volume"]) if "volume" in latest_data else None
                    print(f"  💰 Current VN-Index: {current_price}")
                    print(f"  📈 Volume: {volume:,.0f}" if volume else "  📈 Volume: N/A")
                    
                    # Get previous close (second to last)
                    if len(hist_data) > 1:
                        previous_data = hist_data.iloc[-2]
                        previous_close = float(previous_data["close"])
                        print(f"  📉 Previous close: {previous_close}")
                        
                        change = current_price - previous_close
                        change_pct = (change / previous_close) * 100
                        print(f"  📊 Change: {change:+.2f} ({change_pct:+.2f}%)")
                    else:
                        print(f"  📉 Previous close: Same as current")
                    
                    print(f"  ✅ Success with source: {source}")
                    return True
                else:
                    print(f"  ❌ No historical data from {source}")
                    
            except Exception as e:
                print(f"  ❌ Error with {source}: {e}")
                continue
        
        print("\n❌ Could not get VN-Index data from any source")
        return False
        
    except Exception as e:
        print(f"❌ Error importing vnstock: {e}")
        return False

async def main():
    """Run test"""
    print("🚀 Testing VN-Index Data Retrieval...")
    print("=" * 60)
    
    success = await test_vnindex_data()
    
    if success:
        print("\n✅ VN-Index data retrieval successful!")
    else:
        print("\n❌ VN-Index data retrieval failed!")
        print("💡 This explains why the target range shows 1200-1250 instead of real data")

if __name__ == "__main__":
    asyncio.run(main())
