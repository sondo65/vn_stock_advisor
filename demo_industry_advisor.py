"""
Demo Industry Stock Advisor - Demo chức năng gợi ý cổ phiếu theo ngành

Script demo để test và sử dụng chức năng gợi ý cổ phiếu theo ngành
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from vn_stock_advisor.scanner import (
    IndustryStockAdvisor,
    suggest_industry_stocks,
    get_top_industry_opportunities,
    compare_industries,
    get_available_industries
)

def print_separator(title: str = ""):
    """Print separator with title"""
    print("\n" + "="*80)
    if title:
        print(f" {title}")
        print("="*80)
    else:
        print("="*80)

def print_industry_recommendation(recommendation):
    """Print industry recommendation in a formatted way"""
    print(f"\n🏭 NGÀNH: {recommendation.industry}")
    print(f"📊 Điểm tổng thể: {recommendation.industry_analysis.overall_score:.1f}/10")
    print(f"📈 Xu hướng: {recommendation.industry_analysis.trend.value.upper()}")
    print(f"🎯 Khuyến nghị: {recommendation.industry_analysis.recommendation}")
    print(f"🔍 Độ tin cậy: {recommendation.confidence:.1%}")
    
    print(f"\n📝 Tóm tắt:")
    print(f"   {recommendation.summary}")
    
    print(f"\n💡 Insights chính:")
    for insight in recommendation.key_insights:
        print(f"   • {insight}")
    
    print(f"\n⚠️ Rủi ro:")
    for risk in recommendation.risk_factors[:3]:  # Show top 3
        print(f"   • {risk}")
    
    print(f"\n🎯 Chiến lược đầu tư:")
    print(f"   {recommendation.investment_strategy}")
    
    if recommendation.stock_suggestions:
        print(f"\n📈 Gợi ý cổ phiếu ({len(recommendation.stock_suggestions)} mã):")
        for i, stock in enumerate(recommendation.stock_suggestions[:5], 1):  # Show top 5
            print(f"   {i}. {stock.symbol} - {stock.company_name}")
            print(f"      Điểm: {stock.total_score:.1f}/10 | Khuyến nghị: {stock.recommendation}")
            print(f"      Giá trị: {stock.value_score:.1f} | Momentum: {stock.momentum_score:.1f} | Chất lượng: {stock.quality_score:.1f}")
            if stock.target_price:
                print(f"      Giá mục tiêu: {stock.target_price:,.0f} VND")
            print(f"      Rủi ro: {stock.risk_level} | Độ tin cậy: {stock.confidence:.1%}")
            print()

def demo_industry_suggestions():
    """Demo gợi ý theo ngành"""
    print_separator("DEMO: GỢI Ý CỔ PHIẾU THEO NGÀNH")
    
    try:
        # Get available industries
        industries = get_available_industries()
        print(f"📋 Có {len(industries)} ngành có sẵn:")
        for i, industry in enumerate(industries[:10], 1):  # Show first 10
            print(f"   {i}. {industry}")
        
        # Demo with specific industries
        demo_industries = [
            "Tài chính ngân hàng",
            "Bất động sản", 
            "Phần mềm và dịch vụ công nghệ thông tin"
        ]
        
        for industry in demo_industries:
            if industry in industries:
                print_separator(f"PHÂN TÍCH NGÀNH: {industry}")
                
                try:
                    advisor = IndustryStockAdvisor()
                    recommendation = advisor.get_industry_recommendation(
                        industry=industry,
                        max_stocks=5,
                        min_score=6.5,
                        include_analysis=True
                    )
                    
                    if recommendation:
                        print_industry_recommendation(recommendation)
                    else:
                        print(f"❌ Không tìm thấy gợi ý cho ngành {industry}")
                        
                except Exception as e:
                    print(f"❌ Lỗi phân tích ngành {industry}: {e}")
            else:
                print(f"⚠️ Ngành {industry} không có sẵn")
    
    except Exception as e:
        print(f"❌ Lỗi demo industry suggestions: {e}")

def demo_top_opportunities():
    """Demo top cơ hội đầu tư"""
    print_separator("DEMO: TOP CƠ HỘI ĐẦU TƯ")
    
    try:
        opportunities = get_top_industry_opportunities(
            max_industries=3,
            max_stocks_per_industry=3
        )
        
        if opportunities:
            print(f"🏆 Top {len(opportunities)} cơ hội đầu tư theo ngành:")
            
            for i, opportunity in enumerate(opportunities, 1):
                print(f"\n🏅 #{i} - {opportunity.industry}")
                print(f"   Điểm ngành: {opportunity.industry_analysis.overall_score:.1f}/10")
                print(f"   Khuyến nghị: {opportunity.industry_analysis.recommendation}")
                print(f"   Số cổ phiếu: {len(opportunity.stock_suggestions)}")
                
                if opportunity.stock_suggestions:
                    top_picks = opportunity.stock_suggestions[:3]
                    picks_text = " | ".join([f"{pick.symbol} ({pick.total_score:.1f})" for pick in top_picks])
                    print(f"   Top picks: {picks_text}")
                
                print(f"   Tóm tắt: {opportunity.summary}")
        else:
            print("❌ Không tìm thấy cơ hội đầu tư nào")
    
    except Exception as e:
        print(f"❌ Lỗi demo top opportunities: {e}")

def demo_industry_comparison():
    """Demo so sánh ngành"""
    print_separator("DEMO: SO SÁNH NGÀNH")
    
    try:
        # Compare specific industries
        industries_to_compare = [
            "Tài chính ngân hàng",
            "Bất động sản",
            "Phần mềm và dịch vụ công nghệ thông tin"
        ]
        
        comparisons = compare_industries(
            industries=industries_to_compare,
            max_stocks_per_industry=3
        )
        
        if comparisons:
            print(f"⚖️ So sánh {len(comparisons)} ngành:")
            
            # Create comparison table
            print(f"\n{'Ngành':<40} {'Điểm':<8} {'Khuyến nghị':<12} {'Số CP':<6}")
            print("-" * 80)
            
            for comp in comparisons:
                print(f"{comp.industry:<40} {comp.industry_analysis.overall_score:<8.1f} {comp.industry_analysis.recommendation:<12} {len(comp.stock_suggestions):<6}")
            
            # Show detailed comparison
            print(f"\n🔍 So sánh chi tiết:")
            for comp in comparisons:
                print(f"\n📊 {comp.industry}:")
                print(f"   • Điểm tổng thể: {comp.industry_analysis.overall_score:.1f}/10")
                print(f"   • Momentum: {comp.industry_analysis.momentum_score:.1f}/10")
                print(f"   • Giá trị: {comp.industry_analysis.value_score:.1f}/10")
                print(f"   • Chất lượng: {comp.industry_analysis.quality_score:.1f}/10")
                print(f"   • P/E trung bình: {comp.industry_analysis.avg_pe:.1f}")
                print(f"   • P/B trung bình: {comp.industry_analysis.avg_pb:.1f}")
                
                if comp.stock_suggestions:
                    top_stocks = comp.stock_suggestions[:2]
                    stocks_text = " | ".join([f"{s.symbol} ({s.total_score:.1f})" for s in top_stocks])
                    print(f"   • Top picks: {stocks_text}")
        else:
            print("❌ Không thể so sánh các ngành")
    
    except Exception as e:
        print(f"❌ Lỗi demo industry comparison: {e}")

def demo_quick_functions():
    """Demo các hàm tiện ích"""
    print_separator("DEMO: CÁC HÀM TIỆN ÍCH")
    
    try:
        # Quick industry stock suggestion
        print("🔍 Gợi ý nhanh cổ phiếu ngành Tài chính ngân hàng:")
        stocks = suggest_industry_stocks(
            industry="Tài chính ngân hàng",
            max_stocks=3,
            min_score=7.0
        )
        
        if stocks:
            for stock in stocks:
                print(f"   • {stock.symbol}: {stock.total_score:.1f}/10 ({stock.recommendation})")
        else:
            print("   ❌ Không tìm thấy gợi ý nào")
        
        # Available industries
        print(f"\n📋 Danh sách ngành có sẵn:")
        industries = get_available_industries()
        for i, industry in enumerate(industries[:5], 1):
            print(f"   {i}. {industry}")
        if len(industries) > 5:
            print(f"   ... và {len(industries) - 5} ngành khác")
    
    except Exception as e:
        print(f"❌ Lỗi demo quick functions: {e}")

def main():
    """Main demo function"""
    print_separator("INDUSTRY STOCK ADVISOR - DEMO")
    print(f"🕐 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📊 Demo chức năng gợi ý cổ phiếu theo ngành")
    
    try:
        # Run all demos
        demo_quick_functions()
        demo_industry_suggestions()
        demo_top_opportunities()
        demo_industry_comparison()
        
        print_separator("DEMO HOÀN THÀNH")
        print("✅ Tất cả demo đã chạy thành công!")
        print("💡 Bạn có thể sử dụng giao diện Streamlit: streamlit run industry_stock_advisor_ui.py")
        
    except Exception as e:
        print(f"❌ Lỗi chạy demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
