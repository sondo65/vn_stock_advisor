"""
VN Stock Advisor - Mobile-Responsive Interface
Phase 4: Mobile-first design with PWA capabilities
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import json

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
        tab1, tab2, tab3 = st.tabs(["🔍 Phân tích", "📊 Watchlist", "⚙️ Cài đặt"])
        
        with tab1:
            self.render_analysis_tab()
        
        with tab2:
            self.render_watchlist_tab()
        
        with tab3:
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
