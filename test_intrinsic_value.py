#!/usr/bin/env python3
"""
Test script for intrinsic value calculation functionality.
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram_portfolio_bot import IntrinsicValueCalculator

async def test_intrinsic_value():
    """Test intrinsic value calculation for VN stocks."""
    
    # Test symbols
    test_symbols = ['VIC', 'VCB', 'FPT', 'VNM', 'HPG']
    
    print("🧪 Testing Intrinsic Value Calculation")
    print("=" * 50)
    
    for symbol in test_symbols:
        print(f"\n📊 Testing {symbol}...")
        
        try:
            # Get financial data
            print(f"  🔄 Getting financial data for {symbol}...")
            financial_data = await IntrinsicValueCalculator.get_financial_data(symbol)
            
            if not financial_data:
                print(f"  ❌ No financial data available for {symbol}")
                continue
                
            print(f"  ✅ Financial data retrieved:")
            print(f"    • Current Price: {financial_data['current_price']:,.0f} VND")
            print(f"    • EPS: {financial_data['eps']:,.0f} VND")
            print(f"    • Book Value/Share: {financial_data['book_value_per_share']:,.0f} VND")
            print(f"    • ROE: {financial_data['roe']:.1%}")
            print(f"    • Avg Growth Rate: {financial_data['avg_growth_rate']:.1%}")
            
            # Test DCF method
            print(f"  🔄 Calculating DCF intrinsic value...")
            dcf_result = IntrinsicValueCalculator.calculate_dcf_intrinsic_value(financial_data)
            if dcf_result:
                print(f"    • DCF Intrinsic Value: {dcf_result['intrinsic_value']:,.0f} VND")
                print(f"    • Discount Rate: {dcf_result['discount_rate']:.1%}")
                print(f"    • Growth Rate: {dcf_result['growth_rate']:.1%}")
            else:
                print(f"    ❌ DCF calculation failed")
            
            # Test P/E method
            print(f"  🔄 Calculating P/E intrinsic value...")
            pe_result = IntrinsicValueCalculator.calculate_pe_intrinsic_value(financial_data)
            if pe_result:
                print(f"    • P/E Intrinsic Value: {pe_result['intrinsic_value']:,.0f} VND")
                print(f"    • Target P/E: {pe_result['target_pe']:.1f}")
                print(f"    • ROE: {pe_result['roe']:.1%}")
            else:
                print(f"    ❌ P/E calculation failed")
            
            # Test Graham method
            print(f"  🔄 Calculating Graham intrinsic value...")
            graham_result = IntrinsicValueCalculator.calculate_graham_intrinsic_value(financial_data)
            if graham_result:
                print(f"    • Graham Intrinsic Value: {graham_result['intrinsic_value']:,.0f} VND")
                print(f"    • Graham Value: {graham_result['graham_value']:,.0f} VND")
                print(f"    • Max Value: {graham_result['max_value']:,.0f} VND")
            else:
                print(f"    ❌ Graham calculation failed")
            
            # Test weighted average
            if dcf_result and pe_result and graham_result:
                print(f"  🔄 Calculating weighted average...")
                weighted_result = IntrinsicValueCalculator.calculate_weighted_intrinsic_value(
                    dcf_result, pe_result, graham_result
                )
                if weighted_result:
                    print(f"    • Weighted Intrinsic Value: {weighted_result['intrinsic_value']:,.0f} VND")
                    print(f"    • DCF Weight: 50%, P/E Weight: 30%, Graham Weight: 20%")
            
            # Test safety margin
            if dcf_result:
                intrinsic_value = dcf_result['intrinsic_value']
                current_price = financial_data['current_price']
                safety_analysis = IntrinsicValueCalculator.calculate_safety_margin(
                    intrinsic_value, current_price
                )
                if safety_analysis:
                    print(f"  🛡️ Safety Analysis:")
                    print(f"    • Recommendation: {safety_analysis['recommendation']}")
                    print(f"    • Risk Level: {safety_analysis['risk_level']}")
                    if safety_analysis['is_undervalued']:
                        print(f"    • Discount: {safety_analysis['discount_pct']:.1f}%")
                        print(f"    • Safe Buy Price: {safety_analysis['safe_buy_price']:,.0f} VND")
                    elif safety_analysis['is_overvalued']:
                        print(f"    • Premium: {safety_analysis['premium_pct']:.1f}%")
            
            # Test sensitivity analysis
            if dcf_result:
                print(f"  🔄 Generating sensitivity analysis...")
                sensitivity = IntrinsicValueCalculator.generate_sensitivity_analysis(
                    financial_data, dcf_result['intrinsic_value']
                )
                if sensitivity:
                    print(f"    • Discount Rate Range: {sensitivity['discount_rates'][0]:.0%} - {sensitivity['discount_rates'][-1]:.0%}")
                    print(f"    • Growth Rate Range: {sensitivity['growth_rates'][0]:.0%} - {sensitivity['growth_rates'][-1]:.0%}")
                    
                    # Show value range
                    all_values = [val for row in sensitivity['sensitivity_matrix'] for val in row if val > 0]
                    if all_values:
                        min_val = min(all_values)
                        max_val = max(all_values)
                        print(f"    • Value Range: {min_val:,.0f} - {max_val:,.0f} VND")
            
            print(f"  ✅ {symbol} analysis completed successfully!")
            
        except Exception as e:
            print(f"  ❌ Error analyzing {symbol}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Intrinsic value testing completed!")

if __name__ == "__main__":
    asyncio.run(test_intrinsic_value())
