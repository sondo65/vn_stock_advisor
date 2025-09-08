#!/usr/bin/env python3
"""
Manual test for P/E calculation
"""
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_manual_pe_calculation():
    """Manual test for P/E calculation"""
    print("=== Manual P/E Calculation Test ===")
    
    try:
        from vnstock import Vnstock
        print("✅ Vnstock imported successfully")
        
        # Test với MSB
        symbol = "MSB"
        print(f"\nTesting with {symbol}...")
        
        # Lấy dữ liệu từ VCI
        try:
            stock = Vnstock().stock(symbol=symbol, source="VCI")
            print("✅ Stock data loaded from VCI")
            
            # Lấy financial ratios
            try:
                ratios = stock.finance.ratio(period="quarter")
                print(f"✅ Financial ratios loaded: {len(ratios)} records")
                
                if not ratios.empty:
                    latest_ratios = ratios.iloc[0]
                    print(f"Latest ratios columns: {list(latest_ratios.index)}")
                    
                    # Tìm P/E
                    pe_ratio = None
                    for key in latest_ratios.index:
                        if 'P/E' in str(key) or 'pe' in str(key).lower():
                            pe_ratio = latest_ratios[key]
                            print(f"Found P/E: {key} = {pe_ratio}")
                            break
                    
                    if pe_ratio is None:
                        print("❌ P/E not found in ratios")
                    else:
                        print(f"✅ P/E from source: {pe_ratio}")
                
            except Exception as e:
                print(f"❌ Financial ratios error: {e}")
            
            # Lấy income statement
            try:
                income = stock.finance.income_statement(period="quarter")
                print(f"✅ Income statement loaded: {len(income)} records")
                
                if not income.empty:
                    print(f"Income statement columns: {list(income.columns)}")
                    
                    # Tìm net income
                    net_income = None
                    for col in income.columns:
                        if 'Net Profit' in str(col) or 'net income' in str(col).lower():
                            net_income = income[col].iloc[0]
                            print(f"Found Net Income: {col} = {net_income}")
                            break
                    
                    if net_income is None:
                        print("❌ Net Income not found")
                    else:
                        print(f"✅ Net Income: {net_income}")
                
            except Exception as e:
                print(f"❌ Income statement error: {e}")
            
            # Lấy quote history
            try:
                from datetime import datetime, timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
                quote_history = stock.quote.history(
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                    interval="1D"
                )
                print(f"✅ Quote history loaded: {len(quote_history)} records")
                
                if not quote_history.empty:
                    closes = quote_history["close"].dropna()
                    if not closes.empty:
                        current_price = float(closes.iloc[-1])
                        print(f"✅ Current price: {current_price:,.0f} VND")
                    else:
                        print("❌ No close prices found")
                else:
                    print("❌ Quote history is empty")
                
            except Exception as e:
                print(f"❌ Quote history error: {e}")
                
        except Exception as e:
            print(f"❌ Stock data error: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_manual_pe_calculation()
