"""
Industry Stock Advisor UI - Giao diện gợi ý cổ phiếu theo ngành

Streamlit app để sử dụng chức năng gợi ý cổ phiếu theo ngành
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
from typing import List, Dict, Any

# Import our modules
try:
    from src.vn_stock_advisor.scanner import (
        IndustryStockAdvisor,
        suggest_industry_stocks,
        get_top_industry_opportunities,
        compare_industries,
        get_available_industries
    )
    MODULES_AVAILABLE = True
except ImportError as e:
    st.error(f"Không thể import modules: {e}")
    MODULES_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Industry Stock Advisor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .recommendation-buy {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .recommendation-hold {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .recommendation-sell {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application"""
    
    # Header
    st.markdown('<h1 class="main-header">📊 Industry Stock Advisor</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <p style="font-size: 1.2rem; color: #666;">
            Gợi ý cổ phiếu tiềm năng dựa trên phân tích kỹ thuật và số liệu thực tế theo từng ngành
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if not MODULES_AVAILABLE:
        st.error("❌ Không thể khởi tạo hệ thống. Vui lòng kiểm tra cài đặt modules.")
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Cài đặt")
        
        # Analysis options
        st.markdown("### 📈 Tùy chọn phân tích")
        max_stocks = st.slider("Số cổ phiếu tối đa", 5, 20, 10)
        min_score = st.slider("Điểm tối thiểu", 5.0, 9.0, 7.0, 0.1)
        include_analysis = st.checkbox("Bao gồm phân tích chi tiết", value=True)
        
        # Cache options
        st.markdown("### 💾 Cache")
        if st.button("Xóa cache"):
            try:
                advisor = IndustryStockAdvisor()
                advisor.clear_cache()
                st.success("✅ Đã xóa cache")
            except Exception as e:
                st.error(f"❌ Lỗi xóa cache: {e}")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏭 Gợi ý theo ngành", 
        "🏆 Top cơ hội", 
        "⚖️ So sánh ngành", 
        "📋 Danh sách ngành"
    ])
    
    with tab1:
        show_industry_suggestions(max_stocks, min_score, include_analysis)
    
    with tab2:
        show_top_opportunities(max_stocks, min_score)
    
    with tab3:
        show_industry_comparison(max_stocks, min_score)
    
    with tab4:
        show_industry_list()

def show_industry_suggestions(max_stocks: int, min_score: float, include_analysis: bool):
    """Hiển thị gợi ý theo ngành"""
    st.markdown('<h2 class="section-header">🏭 Gợi ý cổ phiếu theo ngành</h2>', unsafe_allow_html=True)
    
    # Get available industries
    try:
        available_industries = get_available_industries()
    except Exception as e:
        st.error(f"❌ Không thể lấy danh sách ngành: {e}")
        return
    
    # Industry selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_industry = st.selectbox(
            "Chọn ngành:",
            available_industries,
            help="Chọn ngành để xem gợi ý cổ phiếu"
        )
    
    with col2:
        if st.button("🔍 Phân tích", type="primary"):
            analyze_industry(selected_industry, max_stocks, min_score, include_analysis)

def analyze_industry(industry: str, max_stocks: int, min_score: float, include_analysis: bool):
    """Phân tích ngành và hiển thị kết quả"""
    
    with st.spinner(f"🔄 Đang phân tích ngành {industry}..."):
        try:
            advisor = IndustryStockAdvisor()
            recommendation = advisor.get_industry_recommendation(
                industry=industry,
                max_stocks=max_stocks,
                min_score=min_score,
                include_analysis=include_analysis
            )
            
            if not recommendation:
                st.warning(f"⚠️ Không tìm thấy gợi ý nào cho ngành {industry}")
                return
            
            # Display results
            display_industry_recommendation(recommendation)
            
        except Exception as e:
            st.error(f"❌ Lỗi phân tích ngành: {e}")

def display_industry_recommendation(recommendation):
    """Hiển thị khuyến nghị ngành"""
    
    # Industry overview
    st.markdown('<h3 class="section-header">📊 Tổng quan ngành</h3>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Điểm tổng thể",
            f"{recommendation.industry_analysis.overall_score:.1f}/10",
            delta=f"{recommendation.industry_analysis.overall_score - 7.0:.1f}"
        )
    
    with col2:
        st.metric(
            "Xu hướng",
            recommendation.industry_analysis.trend.value.upper(),
            delta=None
        )
    
    with col3:
        st.metric(
            "Khuyến nghị",
            recommendation.industry_analysis.recommendation,
            delta=None
        )
    
    with col4:
        st.metric(
            "Độ tin cậy",
            f"{recommendation.confidence:.1%}",
            delta=None
        )
    
    # Summary
    st.markdown("### 📝 Tóm tắt")
    st.info(recommendation.summary)
    
    # Key insights
    st.markdown("### 💡 Insights chính")
    for insight in recommendation.key_insights:
        st.markdown(f"• {insight}")
    
    # Risk factors
    st.markdown("### ⚠️ Rủi ro")
    for risk in recommendation.risk_factors:
        st.markdown(f"• {risk}")
    
    # Investment strategy
    st.markdown("### 🎯 Chiến lược đầu tư")
    st.success(recommendation.investment_strategy)
    
    # Stock suggestions
    st.markdown('<h3 class="section-header">📈 Gợi ý cổ phiếu</h3>', unsafe_allow_html=True)
    
    if recommendation.stock_suggestions:
        # Create DataFrame for display
        stocks_data = []
        for stock in recommendation.stock_suggestions:
            stocks_data.append({
                "Mã": stock.symbol,
                "Tên công ty": stock.company_name,
                "Điểm tổng": f"{stock.total_score:.1f}",
                "Điểm giá trị": f"{stock.value_score:.1f}",
                "Điểm momentum": f"{stock.momentum_score:.1f}",
                "Điểm chất lượng": f"{stock.quality_score:.1f}",
                "Khuyến nghị": stock.recommendation,
                "Độ tin cậy": f"{stock.confidence:.1%}",
                "Rủi ro": stock.risk_level,
                "Giá mục tiêu": f"{stock.target_price:,.0f}" if stock.target_price else "N/A"
            })
        
        df = pd.DataFrame(stocks_data)
        
        # Display table with styling
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Score distribution
            fig_scores = px.bar(
                df,
                x="Mã",
                y=["Điểm giá trị", "Điểm momentum", "Điểm chất lượng"],
                title="Phân bố điểm số",
                barmode="group"
            )
            st.plotly_chart(fig_scores, use_container_width=True)
        
        with col2:
            # Recommendation distribution
            rec_counts = df["Khuyến nghị"].value_counts()
            fig_rec = px.pie(
                values=rec_counts.values,
                names=rec_counts.index,
                title="Phân bố khuyến nghị"
            )
            st.plotly_chart(fig_rec, use_container_width=True)
        
        # Detailed analysis for each stock
        if include_analysis:
            st.markdown("### 🔍 Phân tích chi tiết")
            
            for i, stock in enumerate(recommendation.stock_suggestions[:5]):  # Show top 5
                with st.expander(f"📊 {stock.symbol} - {stock.company_name} (Điểm: {stock.total_score:.1f})"):
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📈 Phân tích định giá:**")
                        st.write(stock.valuation_analysis)
                        
                        st.markdown("**📊 Phân tích kỹ thuật:**")
                        st.write(stock.technical_analysis)
                    
                    with col2:
                        st.markdown("**🏭 Vị thế ngành:**")
                        st.write(stock.industry_position)
                        
                        st.markdown("**🚀 Tiềm năng tăng trưởng:**")
                        st.write(stock.growth_potential)
    else:
        st.warning("⚠️ Không có gợi ý cổ phiếu nào đạt tiêu chí")

def show_top_opportunities(max_stocks: int, min_score: float):
    """Hiển thị top cơ hội đầu tư"""
    st.markdown('<h2 class="section-header">🏆 Top cơ hội đầu tư theo ngành</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        max_industries = st.slider("Số ngành tối đa", 3, 10, 5)
    
    with col2:
        if st.button("🔍 Tìm cơ hội", type="primary"):
            get_top_opportunities_analysis(max_industries, max_stocks, min_score)

def get_top_opportunities_analysis(max_industries: int, max_stocks: int, min_score: float):
    """Lấy và hiển thị top cơ hội"""
    
    with st.spinner("🔄 Đang tìm kiếm top cơ hội đầu tư..."):
        try:
            opportunities = get_top_industry_opportunities(
                max_industries=max_industries,
                max_stocks_per_industry=max_stocks
            )
            
            if not opportunities:
                st.warning("⚠️ Không tìm thấy cơ hội đầu tư nào")
                return
            
            # Display opportunities
            for i, opportunity in enumerate(opportunities, 1):
                with st.container():
                    st.markdown(f"### 🏅 #{i} - {opportunity.industry}")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Điểm ngành", f"{opportunity.industry_analysis.overall_score:.1f}/10")
                    
                    with col2:
                        st.metric("Khuyến nghị", opportunity.industry_analysis.recommendation)
                    
                    with col3:
                        st.metric("Số cổ phiếu", len(opportunity.stock_suggestions))
                    
                    # Top picks
                    if opportunity.stock_suggestions:
                        top_picks = opportunity.stock_suggestions[:3]
                        picks_text = " | ".join([f"{pick.symbol} ({pick.total_score:.1f})" for pick in top_picks])
                        st.markdown(f"**Top picks:** {picks_text}")
                    
                    st.markdown(f"**Tóm tắt:** {opportunity.summary}")
                    
                    st.divider()
            
        except Exception as e:
            st.error(f"❌ Lỗi tìm kiếm cơ hội: {e}")

def show_industry_comparison(max_stocks: int, min_score: float):
    """Hiển thị so sánh ngành"""
    st.markdown('<h2 class="section-header">⚖️ So sánh ngành</h2>', unsafe_allow_html=True)
    
    # Get available industries
    try:
        available_industries = get_available_industries()
    except Exception as e:
        st.error(f"❌ Không thể lấy danh sách ngành: {e}")
        return
    
    # Industry selection
    selected_industries = st.multiselect(
        "Chọn các ngành để so sánh:",
        available_industries,
        default=available_industries[:3] if len(available_industries) >= 3 else available_industries,
        help="Chọn ít nhất 2 ngành để so sánh"
    )
    
    if len(selected_industries) < 2:
        st.warning("⚠️ Vui lòng chọn ít nhất 2 ngành để so sánh")
        return
    
    if st.button("⚖️ So sánh", type="primary"):
        compare_industries_analysis(selected_industries, max_stocks, min_score)

def compare_industries_analysis(industries: List[str], max_stocks: int, min_score: float):
    """So sánh các ngành"""
    
    with st.spinner("🔄 Đang so sánh các ngành..."):
        try:
            comparisons = compare_industries(
                industries=industries,
                max_stocks_per_industry=max_stocks
            )
            
            if not comparisons:
                st.warning("⚠️ Không thể so sánh các ngành")
                return
            
            # Create comparison chart
            comparison_data = []
            for comp in comparisons:
                comparison_data.append({
                    "Ngành": comp.industry,
                    "Điểm tổng thể": comp.industry_analysis.overall_score,
                    "Điểm momentum": comp.industry_analysis.momentum_score,
                    "Điểm giá trị": comp.industry_analysis.value_score,
                    "Điểm chất lượng": comp.industry_analysis.quality_score,
                    "Khuyến nghị": comp.industry_analysis.recommendation,
                    "Số cổ phiếu": len(comp.stock_suggestions)
                })
            
            df_comparison = pd.DataFrame(comparison_data)
            
            # Display comparison table
            st.markdown("### 📊 Bảng so sánh")
            st.dataframe(df_comparison, use_container_width=True, hide_index=True)
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Overall score comparison
                fig_overall = px.bar(
                    df_comparison,
                    x="Ngành",
                    y="Điểm tổng thể",
                    title="So sánh điểm tổng thể",
                    color="Điểm tổng thể",
                    color_continuous_scale="RdYlGn"
                )
                fig_overall.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_overall, use_container_width=True)
            
            with col2:
                # Score breakdown
                fig_breakdown = px.bar(
                    df_comparison,
                    x="Ngành",
                    y=["Điểm momentum", "Điểm giá trị", "Điểm chất lượng"],
                    title="Phân tích điểm số",
                    barmode="group"
                )
                fig_breakdown.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_breakdown, use_container_width=True)
            
            # Detailed comparison
            st.markdown("### 🔍 So sánh chi tiết")
            
            for comp in comparisons:
                with st.expander(f"📊 {comp.industry} - Điểm: {comp.industry_analysis.overall_score:.1f}"):
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📈 Điểm số:**")
                        st.write(f"• Tổng thể: {comp.industry_analysis.overall_score:.1f}/10")
                        st.write(f"• Momentum: {comp.industry_analysis.momentum_score:.1f}/10")
                        st.write(f"• Giá trị: {comp.industry_analysis.value_score:.1f}/10")
                        st.write(f"• Chất lượng: {comp.industry_analysis.quality_score:.1f}/10")
                        
                        st.markdown("**📊 Thống kê:**")
                        st.write(f"• P/E trung bình: {comp.industry_analysis.avg_pe:.1f}")
                        st.write(f"• P/B trung bình: {comp.industry_analysis.avg_pb:.1f}")
                        st.write(f"• ROE trung bình: {comp.industry_analysis.avg_roe:.1f}%")
                    
                    with col2:
                        st.markdown("**💡 Insights:**")
                        for insight in comp.key_insights:
                            st.write(f"• {insight}")
                        
                        st.markdown("**⚠️ Rủi ro:**")
                        for risk in comp.risk_factors[:3]:  # Show top 3 risks
                            st.write(f"• {risk}")
                    
                    # Top stocks
                    if comp.stock_suggestions:
                        st.markdown("**🏆 Top cổ phiếu:**")
                        top_stocks = comp.stock_suggestions[:3]
                        for stock in top_stocks:
                            st.write(f"• {stock.symbol}: {stock.total_score:.1f}/10 ({stock.recommendation})")
            
        except Exception as e:
            st.error(f"❌ Lỗi so sánh ngành: {e}")

def show_industry_list():
    """Hiển thị danh sách ngành"""
    st.markdown('<h2 class="section-header">📋 Danh sách ngành có sẵn</h2>', unsafe_allow_html=True)
    
    try:
        available_industries = get_available_industries()
        
        if not available_industries:
            st.warning("⚠️ Không có ngành nào có sẵn")
            return
        
        # Display industries in columns
        cols = st.columns(3)
        
        for i, industry in enumerate(available_industries):
            with cols[i % 3]:
                st.markdown(f"• {industry}")
        
        # Industry summary
        st.markdown("### 📊 Thông tin ngành")
        
        try:
            advisor = IndustryStockAdvisor()
            
            # Create summary data
            summary_data = []
            for industry in available_industries[:10]:  # Show first 10
                try:
                    summary = advisor.get_industry_summary(industry)
                    if "error" not in summary:
                        summary_data.append({
                            "Ngành": industry,
                            "Số cổ phiếu": summary["stock_count"],
                            "P/E ngành": summary["benchmark"]["pe_ratio"],
                            "P/B ngành": summary["benchmark"]["pb_ratio"],
                            "ROE ngành": summary["benchmark"]["roe"],
                            "Biến động": summary["benchmark"]["volatility"] or "N/A"
                        })
                except Exception as e:
                    st.warning(f"⚠️ Không thể lấy thông tin ngành {industry}: {e}")
            
            if summary_data:
                df_summary = pd.DataFrame(summary_data)
                st.dataframe(df_summary, use_container_width=True, hide_index=True)
            
        except Exception as e:
            st.warning(f"⚠️ Không thể lấy thông tin chi tiết: {e}")
    
    except Exception as e:
        st.error(f"❌ Lỗi lấy danh sách ngành: {e}")

if __name__ == "__main__":
    main()
