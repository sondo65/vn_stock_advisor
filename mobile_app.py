"""
VN Stock Advisor - Mobile-Responsive Interface
Phase 4: Mobile-first design with PWA capabilities
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import json
import pandas as pd
import time

# Import optimized scanner
try:
    from src.vn_stock_advisor.scanner import (
        LightweightStockScanner,
        quick_scan_market,
        find_opportunities
    )
    SCANNER_AVAILABLE = True
except ImportError:
    SCANNER_AVAILABLE = False

# Mobile-first configuration
st.set_page_config(
    page_title="VN Stock Advisor Mobile",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed"  # Mobile-friendly
)

# Mobile CSS
st.markdown("""
<style>
    /* Mobile-first responsive design */
    .main-container {
        padding: 0.5rem;
        max-width: 100%;
    }
    
    .mobile-header {
        background: linear-gradient(90deg, #1f77b4, #17a2b8);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .mobile-card {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    
    .quick-action {
        background: #f8f9fa;
        border: 2px solid #007bff;
        border-radius: 10px;
        padding: 0.75rem;
        margin: 0.25rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .quick-action:hover {
        background: #007bff;
        color: white;
    }
    
    .metric-mobile {
        text-align: center;
        padding: 0.5rem;
        background: #f8f9fa;
        border-radius: 8px;
        margin: 0.25rem;
    }
    
    .recommendation-mobile {
        font-size: 1.2rem;
        font-weight: bold;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
    }
    
    .buy-mobile { background: #d4edda; color: #155724; }
    .hold-mobile { background: #fff3cd; color: #856404; }
    .sell-mobile { background: #f8d7da; color: #721c24; }
    
    /* Hide sidebar on mobile */
    @media (max-width: 768px) {
        .css-1d391kg { display: none; }
        .css-1lcbmhc { margin-left: 0; }
        .css-1outpf7 { padding-left: 1rem; padding-right: 1rem; }
    }
</style>
""", unsafe_allow_html=True)

class MobileStockApp:
    """Mobile-optimized stock analysis app."""
    
    def __init__(self):
        if 'mobile_favorites' not in st.session_state:
            st.session_state.mobile_favorites = ['HPG', 'VIC', 'VCB', 'FPT']
        if 'mobile_analysis' not in st.session_state:
            st.session_state.mobile_analysis = None
    
    def run(self):
        """Run mobile app."""
        # Mobile header
        st.markdown("""
        <div class="mobile-header">
            <h2>📱 VN Stock Advisor Mobile</h2>
            <p>Phân tích cổ phiếu thông minh</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Phân tích", "⚡ Quét Nhanh", "📊 Watchlist", "⚙️ Cài đặt"])
        
        with tab1:
            self.render_analysis_tab()
        
        with tab2:
            self.render_mobile_scanner()
        
        with tab3:
            self.render_watchlist_tab()
        
        with tab4:
            self.render_settings_tab()
    
    def render_analysis_tab(self):
        """Render mobile analysis interface."""
        st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
        
        # Quick stock buttons
        st.markdown("**📈 Cổ phiếu phổ biến:**")
        
        cols = st.columns(4)
        popular_stocks = ['HPG', 'VIC', 'VCB', 'FPT']
        
        for i, stock in enumerate(popular_stocks):
            with cols[i]:
                if st.button(stock, key=f"quick_{stock}", use_container_width=True):
                    self.analyze_stock(stock)
        
        # Stock input
        symbol = st.text_input("Hoặc nhập mã CK:", placeholder="VD: MSN, TCB...")
        
        if st.button("🔍 Phân tích", type="primary", use_container_width=True):
            if symbol:
                self.analyze_stock(symbol.upper())
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display results
        if st.session_state.mobile_analysis:
            self.display_mobile_results()
    
    def analyze_stock(self, symbol: str):
        """Analyze stock for mobile."""
        with st.spinner(f"Đang phân tích {symbol}..."):
            # Demo analysis
            demo_data = {
                'symbol': symbol,
                'recommendation': 'GIỮ',
                'price': 27500,
                'change': 1.85,
                'pe': 15.3,
                'pb': 1.7,
                'rsi': 58.3,
                'trend': 'Tăng',
                'timestamp': datetime.now()
            }
            
            st.session_state.mobile_analysis = demo_data
            st.success(f"✅ Hoàn thành phân tích {symbol}!")
    
    def render_mobile_results(self):
        """Render mobile analysis results."""
        return self.display_mobile_results()
    
    def display_mobile_results(self):
        """Display analysis results optimized for mobile."""
        data = st.session_state.mobile_analysis
        
        # Recommendation card
        rec_class = {
            'MUA': 'buy-mobile',
            'GIỮ': 'hold-mobile', 
            'BÁN': 'sell-mobile'
        }.get(data['recommendation'], 'hold-mobile')
        
        st.markdown(f"""
        <div class="recommendation-mobile {rec_class}">
            🎯 {data['symbol']}: {data['recommendation']}
        </div>
        """, unsafe_allow_html=True)
        
        # Key metrics
        st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Giá", f"{data['price']:,} VND", f"{data['change']:+.1f}%")
            st.metric("P/E", f"{data['pe']}")
        
        with col2:
            st.metric("P/B", f"{data['pb']}")
            st.metric("RSI", f"{data['rsi']}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Quick chart
        self.render_mobile_chart(data)
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⭐ Thêm watchlist", use_container_width=True):
                if data['symbol'] not in st.session_state.mobile_favorites:
                    st.session_state.mobile_favorites.append(data['symbol'])
                    st.success("Đã thêm vào watchlist!")
        
        with col2:
            if st.button("📤 Chia sẻ", use_container_width=True):
                st.info("Tính năng chia sẻ sắp có!")
    
    def render_mobile_chart(self, data):
        """Render mobile-optimized chart."""
        import numpy as np
        
        # Generate sample price data
        np.random.seed(42)
        dates = [datetime.now().date() for _ in range(30)]
        prices = [data['price'] + np.random.normal(0, 500) for _ in range(30)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=prices,
            mode='lines',
            name=data['symbol'],
            line=dict(color='#1f77b4', width=2)
        ))
        
        fig.update_layout(
            height=250,  # Mobile-friendly height
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
            xaxis_title="",
            yaxis_title="Giá (VND)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_watchlist_tab(self):
        """Render mobile watchlist."""
        st.markdown("### 📊 Danh sách theo dõi")
        
        for symbol in st.session_state.mobile_favorites:
            st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown(f"**{symbol}**")
                st.markdown("Demo Company")
            
            with col2:
                price = 25000 + hash(symbol) % 20000
                change = (hash(symbol) % 10) - 5
                st.metric("", f"{price:,}", f"{change:+.1f}%")
            
            with col3:
                if st.button("📊", key=f"analyze_{symbol}"):
                    self.analyze_stock(symbol)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_settings_tab(self):
        """Render mobile settings."""
        st.markdown("### ⚙️ Cài đặt")
        
        st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
        
        st.markdown("**🔔 Thông báo**")
        st.checkbox("Thông báo giá", value=True)
        st.checkbox("Thông báo khuyến nghị", value=False)
        
        st.markdown("**🎨 Giao diện**")
        theme = st.selectbox("Chủ đề", ["Sáng", "Tối", "Tự động"])
        
        st.markdown("**📱 Ứng dụng**")
        st.info("Version: 0.7.0 Mobile")
        
        if st.button("📥 Cài đặt PWA", use_container_width=True):
            st.success("PWA đã được cài đặt!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_mobile_scanner(self):
        """Render mobile-optimized scanner interface."""
        st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
        st.markdown("### ⚡ Quét Nhanh Mobile")
        st.markdown("🎯 Tìm cơ hội đầu tư nhanh chóng")
        
        if not SCANNER_AVAILABLE:
            st.error("❌ Scanner không khả dụng")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Mobile-friendly controls
        scan_preset = st.selectbox(
            "🎯 Chọn preset",
            [
                "🔥 Top cơ hội (VN30)",
                "💎 Cổ phiếu giá trị", 
                "🚀 Momentum mạnh",
                "📈 Tùy chỉnh"
            ],
            key="mobile_scan_preset"
        )
        
        # Custom input for mobile
        if scan_preset == "📈 Tùy chỉnh":
            mobile_stocks = st.text_input(
                "📝 Mã cổ phiếu",
                placeholder="VIC,VCB,FPT",
                key="mobile_custom_stocks"
            )
        
        # Simple scan button
        if st.button("⚡ Quét Ngay", type="primary", use_container_width=True, key="mobile_scan"):
            with st.spinner("🔍 Đang quét..."):
                try:
                    # Prepare stock list based on preset
                    if scan_preset == "🔥 Top cơ hội (VN30)":
                        stock_list = ['VIC', 'VCB', 'FPT', 'HPG', 'VNM', 'MSN', 'MWG', 'TCB', 'BID', 'ACB']
                        min_score = 6.5
                    elif scan_preset == "💎 Cổ phiếu giá trị":
                        stock_list = ['HPG', 'CTG', 'VCB', 'BID', 'TCB', 'STB', 'VIC', 'VHM']
                        min_score = 6.0
                    elif scan_preset == "🚀 Momentum mạnh":
                        stock_list = ['FPT', 'VNM', 'MSN', 'MWG', 'VJC', 'SAB', 'VIC', 'HPG']
                        min_score = 6.5
                    else:  # Tùy chỉnh
                        if not mobile_stocks:
                            st.error("❌ Vui lòng nhập mã cổ phiếu")
                            return
                        stock_list = [s.strip().upper() for s in mobile_stocks.split(',') if s.strip()]
                        min_score = 5.5
                    
                    # Run lightweight scan
                    scanner = LightweightStockScanner(max_workers=2, use_cache=True)
                    
                    start_time = time.time()
                    results = scanner.scan_stocks_lightweight(
                        stock_list=stock_list,
                        min_score=min_score,
                        only_buy_watch=True,
                        max_results=10
                    )
                    scan_time = time.time() - start_time
                    
                    if results:
                        st.success(f"✅ {len(results)} cơ hội trong {scan_time:.1f}s")
                        
                        # Mobile-friendly results display
                        for i, stock in enumerate(results[:5], 1):
                            with st.container():
                                st.markdown(f"""
                                <div class="mobile-card" style="margin: 0.5rem 0; padding: 1rem; border-left: 4px solid {'#28a745' if stock.recommendation == 'BUY' else '#ffc107'};">
                                    <h4>{i}. {stock.symbol} - {stock.recommendation}</h4>
                                    <p><strong>Điểm:</strong> {stock.overall_score:.1f}/10 | 
                                       <strong>P/B:</strong> {stock.pb_ratio:.2f} | 
                                       <strong>RSI:</strong> {stock.rsi:.1f}</p>
                                    <p><small>{stock.macd_signal.title()} MACD, {stock.ma_trend} trend</small></p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Quick action button
                                if st.button(f"📈 Phân tích {stock.symbol}", key=f"mobile_analyze_{stock.symbol}"):
                                    st.info(f"🔄 Đang phân tích {stock.symbol}...")
                                    # Store selected stock for detailed analysis
                                    st.session_state.mobile_selected_stock = stock.symbol
                                    st.session_state.mobile_show_analysis = True
                        
                        # Summary stats
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        with col1:
                            buy_count = len([r for r in results if r.recommendation == "BUY"])
                            st.metric("🟢 BUY", buy_count)
                        with col2:
                            avg_score = sum(r.overall_score for r in results) / len(results)
                            st.metric("⭐ Điểm TB", f"{avg_score:.1f}")
                    
                    else:
                        st.warning("⚠️ Không tìm thấy cơ hội phù hợp")
                        st.info("💡 Thử preset khác hoặc giảm tiêu chí")
                
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
                    if "rate limit" in str(e).lower():
                        st.info("⏱️ API limit. Thử lại sau 1-2 phút")
        
        # Quick tips for mobile users
        with st.expander("💡 Mẹo sử dụng"):
            st.markdown("""
            **⚡ Quét Nhanh:**
            - Chọn preset phù hợp với mục tiêu đầu tư
            - Kết quả hiển thị theo độ ưu tiên
            - Chạm vào cổ phiếu để phân tích chi tiết
            
            **🎯 Preset giải thích:**
            - 🔥 Top cơ hội: Cổ phiếu VN30 có tiềm năng
            - 💎 Giá trị: Tập trung P/B thấp, định giá hấp dẫn
            - 🚀 Momentum: Xu hướng tăng mạnh, breakout potential
            """)
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main function for mobile app."""
    app = MobileStockApp()
    app.run()
    
    # PWA manifest
    st.markdown("""
    <script>
    // PWA Service Worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js');
    }
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
