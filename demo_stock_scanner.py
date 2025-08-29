#!/usr/bin/env python3
"""
Demo Script for Stock Scanner
Demonstrates the stock scanning functionality
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def demo_stock_scanner():
    """Demo the stock scanner functionality."""
    print("🔍 VN Stock Advisor - Stock Scanner Demo")
    print("=" * 50)
    
    try:
        from vn_stock_advisor.scanner import StockScanner, RankingSystem
        
        print("✅ Stock Scanner modules imported successfully")
        
        # Initialize scanner
        scanner = StockScanner(max_workers=1)  # Conservative for demo
        ranking_system = RankingSystem()
        
        print("\n📊 Available scan options:")
        print("1. VN30 stocks")
        print("2. HNX30 stocks") 
        print("3. Custom list")
        
        # Demo with a small custom list (since API key is expired)
        print("\n🚀 Running demo scan with custom list...")
        
        custom_stocks = ['HPG', 'VIC', 'VCB', 'MSN', 'FPT']
        
        print(f"📝 Scanning stocks: {', '.join(custom_stocks)}")
        print("⚠️  Note: This is a demo - actual scanning requires valid API key")
        
        # Simulate scan results
        demo_results = [
            {
                'symbol': 'HPG',
                'total_score': 8.5,
                'decision': 'MUA',
                'buy_price': 27000,
                'sell_price': 32000,
                'analysis_date': datetime.now().isoformat(),
                'raw_data': {
                    'fund_reasoning': 'P/E hợp lý, P/B hấp dẫn, ROE cao',
                    'tech_reasoning': 'Xu hướng tăng, RSI tốt, MACD tích cực',
                    'decision': 'MUA'
                }
            },
            {
                'symbol': 'VIC',
                'total_score': 8.2,
                'decision': 'MUA',
                'buy_price': 45000,
                'sell_price': 52000,
                'analysis_date': datetime.now().isoformat(),
                'raw_data': {
                    'fund_reasoning': 'Doanh thu tăng trưởng mạnh, biên lợi nhuận ổn định',
                    'tech_reasoning': 'Vượt kháng cự, khối lượng tốt',
                    'decision': 'MUA'
                }
            },
            {
                'symbol': 'VCB',
                'total_score': 7.8,
                'decision': 'MUA', 
                'buy_price': 95000,
                'sell_price': 108000,
                'analysis_date': datetime.now().isoformat(),
                'raw_data': {
                    'fund_reasoning': 'ROE cao, tăng trưởng ổn định',
                    'tech_reasoning': 'Xu hướng tăng dài hạn',
                    'decision': 'MUA'
                }
            }
        ]
        
        # Filter results (min_score = 7.5)
        min_score = 7.5
        filtered_results = [r for r in demo_results if r['total_score'] >= min_score]
        
        print(f"\n📈 SCAN RESULTS (min_score = {min_score}):")
        print("-" * 60)
        
        if filtered_results:
            for i, result in enumerate(filtered_results, 1):
                symbol = result['symbol']
                score = result['total_score']
                decision = result['decision']
                buy_price = result['buy_price']
                sell_price = result['sell_price']
                potential = ((sell_price - buy_price) / buy_price * 100) if buy_price else 0
                
                print(f"{i:2d}. {symbol:>4} | Score: {score:5.1f} | {decision:>4} | "
                      f"Buy: {buy_price:>8,} | Target: {sell_price:>8,} | "
                      f"Potential: {potential:>5.1f}%")
        
        # Summary statistics
        print(f"\n📊 SUMMARY:")
        print(f"   • Total scanned: {len(custom_stocks)} stocks")
        print(f"   • Buy recommendations: {len(filtered_results)} stocks")
        
        if filtered_results:
            avg_score = sum(r['total_score'] for r in filtered_results) / len(filtered_results)
            max_score = max(r['total_score'] for r in filtered_results)
            
            potential_gains = []
            for r in filtered_results:
                if r['buy_price'] and r['sell_price']:
                    gain = (r['sell_price'] - r['buy_price']) / r['buy_price'] * 100
                    potential_gains.append(gain)
            
            avg_potential = sum(potential_gains) / len(potential_gains) if potential_gains else 0
            
            print(f"   • Average score: {avg_score:.1f}")
            print(f"   • Highest score: {max_score:.1f}")
            print(f"   • Average potential gain: {avg_potential:.1f}%")
        
        # Generate ranking summary
        print(f"\n📋 RANKING SUMMARY:")
        print("-" * 40)
        summary = ranking_system.generate_ranking_summary(filtered_results)
        print(summary)
        
        # Export demo
        print(f"\n💾 EXPORT DEMO:")
        print("   • JSON export: Available")
        print("   • CSV export: Available") 
        print("   • Summary report: Available")
        
        print(f"\n✅ Demo completed successfully!")
        print(f"🔧 To use with real data, update your Gemini API key in .env file")
        
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        print("💡 Make sure to install the project: pip install -e .")
    
    except Exception as e:
        print(f"❌ Demo error: {e}")

def demo_ranking_system():
    """Demo the ranking system functionality."""
    print("\n🏆 RANKING SYSTEM DEMO")
    print("=" * 30)
    
    try:
        from vn_stock_advisor.scanner import RankingSystem
        
        ranking_system = RankingSystem()
        
        # Test scoring
        sample_reasoning = """
        P/E là 15.3, tương đương với mức trung bình ngành. 
        P/B là 1.7, thấp hơn trung bình ngành (2.82), cho thấy định giá hấp dẫn.
        ROE là 11.7%, ở mức trung bình tốt.
        Biên lợi nhuận 18.4% cho thấy quản lý chi phí hiệu quả.
        """
        
        fund_score = ranking_system.calculate_fundamental_score(sample_reasoning)
        print(f"📊 Fundamental score: {fund_score:.1f}/10")
        
        tech_reasoning = """
        Xu hướng dài hạn tăng, giá trên SMA 200.
        RSI ở mức 41.67 (trung tính).
        MACD dưới Signal Line (tiêu cực).
        Khối lượng giao dịch bình thường.
        """
        
        tech_score = ranking_system.calculate_technical_score(tech_reasoning)
        print(f"📈 Technical score: {tech_score:.1f}/10")
        
        # Test total score calculation
        decision_data = {
            'fund_reasoning': sample_reasoning,
            'tech_reasoning': tech_reasoning,
            'macro_reasoning': 'Không có thông tin vĩ mô cụ thể',
            'decision': 'MUA'
        }
        
        total_score = ranking_system.calculate_total_score(decision_data)
        print(f"⭐ Total weighted score: {total_score:.1f}/10")
        
        print("✅ Ranking system demo completed!")
        
    except Exception as e:
        print(f"❌ Ranking demo error: {e}")

if __name__ == "__main__":
    print("🚀 Starting VN Stock Advisor Scanner Demo...")
    print("=" * 60)
    
    # Run demos
    demo_stock_scanner()
    demo_ranking_system()
    
    print("\n" + "=" * 60)
    print("🎯 Demo completed! Ready to scan stocks when API key is available.")
    print("📚 Check the Streamlit interface and API endpoints for full functionality.")
