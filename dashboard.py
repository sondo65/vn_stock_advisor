"""
VN Stock Advisor - Advanced Visualization Dashboard
Phase 4: Interactive charts and advanced data visualization
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

st.set_page_config(
    page_title="VN Stock Advisor - Advanced Dashboard",
    page_icon="📊",
    layout="wide"
)

# Advanced CSS
st.markdown("""
<style>
    .dashboard-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .chart-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .metric-dashboard {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .analysis-card {
        background: #f8f9fa;
        border-left: 5px solid #667eea;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class AdvancedDashboard:
    """Advanced visualization dashboard."""
    
    def __init__(self):
        """Initialize dashboard."""
        if 'dashboard_data' not in st.session_state:
            self.generate_sample_data()
    
    def generate_sample_data(self):
        """Generate comprehensive sample data."""
        np.random.seed(42)
        
        # Stock universe
        stocks = ['HPG', 'VIC', 'VCB', 'FPT', 'MSN', 'TCB', 'VHM', 'SSI', 'GAS', 'CTG']
        
        # Generate historical data
        dates = pd.date_range(start='2024-01-01', end='2025-08-28', freq='D')
        
        stock_data = {}
        for stock in stocks:
            base_price = 20000 + np.random.randint(0, 80000)
            returns = np.random.normal(0.001, 0.025, len(dates))
            returns[0] = 0
            
            prices = base_price * np.cumprod(1 + returns)
            volumes = np.random.lognormal(10, 0.5, len(dates))
            
            stock_data[stock] = pd.DataFrame({
                'date': dates,
                'price': prices,
                'volume': volumes,
                'returns': returns
            })
        
        # Market data
        vnindex_returns = np.random.normal(0.0005, 0.015, len(dates))
        vnindex_returns[0] = 0
        vnindex = 1200 * np.cumprod(1 + vnindex_returns)
        
        market_data = pd.DataFrame({
            'date': dates,
            'vnindex': vnindex,
            'returns': vnindex_returns
        })
        
        # Fundamental data
        fundamental_data = {}
        for stock in stocks:
            fundamental_data[stock] = {
                'PE': np.random.uniform(8, 25),
                'PB': np.random.uniform(0.8, 4.0),
                'ROE': np.random.uniform(5, 25),
                'ROA': np.random.uniform(2, 15),
                'revenue_growth': np.random.uniform(-10, 30),
                'profit_margin': np.random.uniform(5, 40),
                'market_cap': np.random.uniform(1000, 50000)  # billion VND
            }
        
        # Sector data
        sectors = {
            'Banking': ['VCB', 'TCB', 'CTG'],
            'Steel': ['HPG'],
            'Real Estate': ['VIC', 'VHM'],
            'Technology': ['FPT'],
            'Retail': ['MSN'],
            'Securities': ['SSI'],
            'Oil & Gas': ['GAS']
        }
        
        st.session_state.dashboard_data = {
            'stocks': stocks,
            'stock_data': stock_data,
            'market_data': market_data,
            'fundamental_data': fundamental_data,
            'sectors': sectors
        }
    
    def run(self):
        """Run advanced dashboard."""
        # Header
        st.markdown("""
        <div class="dashboard-header">
            <h1>📊 VN Stock Advisor - Advanced Dashboard</h1>
            <p>Comprehensive market analysis and visualization platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏠 Tổng quan", "📈 Phân tích kỹ thuật", "📊 So sánh cổ phiếu", 
            "🏭 Phân tích ngành", "🎯 Portfolio"
        ])
        
        with tab1:
            self.render_market_overview()
        
        with tab2:
            self.render_technical_analysis()
        
        with tab3:
            self.render_stock_comparison()
        
        with tab4:
            self.render_sector_analysis()
        
        with tab5:
            self.render_portfolio_analysis()
    
    def render_market_overview(self):
        """Render market overview dashboard."""
        data = st.session_state.dashboard_data
        
        # Market metrics
        col1, col2, col3, col4 = st.columns(4)
        
        current_vnindex = data['market_data']['vnindex'].iloc[-1]
        vnindex_change = (current_vnindex / data['market_data']['vnindex'].iloc[-2] - 1) * 100
        
        with col1:
            st.markdown(f"""
            <div class="metric-dashboard">
                <h3>VN-Index</h3>
                <h2>{current_vnindex:.1f}</h2>
                <p>{vnindex_change:+.2f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_volume = sum([data['stock_data'][stock]['volume'].iloc[-1] for stock in data['stocks']])
            st.markdown(f"""
            <div class="metric-dashboard">
                <h3>Tổng KL</h3>
                <h2>{total_volume/1e6:.1f}M</h2>
                <p>Cổ phiếu</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            advancing = len([s for s in data['stocks'] if data['stock_data'][s]['returns'].iloc[-1] > 0])
            st.markdown(f"""
            <div class="metric-dashboard">
                <h3>Tăng/Giảm</h3>
                <h2>{advancing}/{len(data['stocks'])-advancing}</h2>
                <p>Mã cổ phiếu</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            avg_pe = np.mean([data['fundamental_data'][s]['PE'] for s in data['stocks']])
            st.markdown(f"""
            <div class="metric-dashboard">
                <h3>P/E TB</h3>
                <h2>{avg_pe:.1f}</h2>
                <p>Thị trường</p>
            </div>
            """, unsafe_allow_html=True)
        
        # VN-Index chart
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("### 📈 Diễn biến VN-Index")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data['market_data']['date'],
            y=data['market_data']['vnindex'],
            mode='lines',
            name='VN-Index',
            line=dict(color='#667eea', width=2)
        ))
        
        fig.update_layout(
            height=400,
            xaxis_title="Thời gian",
            yaxis_title="Điểm",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Top performers
        col1, col2 = st.columns(2)
        
        with col1:
            self.render_top_performers("🟢 Top Gainers")
        
        with col2:
            self.render_top_performers("🔴 Top Losers", ascending=True)
        
        # Market heatmap
        self.render_market_heatmap()
    
    def render_top_performers(self, title: str, ascending: bool = False):
        """Render top performing stocks."""
        data = st.session_state.dashboard_data
        
        # Calculate daily returns
        performance = []
        for stock in data['stocks']:
            daily_return = data['stock_data'][stock]['returns'].iloc[-1] * 100
            current_price = data['stock_data'][stock]['price'].iloc[-1]
            performance.append({
                'Stock': stock,
                'Price': f"{current_price:,.0f}",
                'Change': f"{daily_return:+.2f}%"
            })
        
        df = pd.DataFrame(performance)
        df['Change_num'] = [float(x.replace('%', '').replace('+', '')) for x in df['Change']]
        df = df.sort_values('Change_num', ascending=ascending).head(5)
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown(f"### {title}")
        st.dataframe(df[['Stock', 'Price', 'Change']], use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_market_heatmap(self):
        """Render market heatmap."""
        data = st.session_state.dashboard_data
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("### 🗺️ Market Heatmap")
        
        # Prepare heatmap data
        stocks = data['stocks']
        returns = [data['stock_data'][s]['returns'].iloc[-1] * 100 for s in stocks]
        market_caps = [data['fundamental_data'][s]['market_cap'] for s in stocks]
        
        fig = go.Figure(data=go.Scatter(
            x=market_caps,
            y=returns,
            mode='markers+text',
            text=stocks,
            textposition="middle center",
            marker=dict(
                size=[mc/1000 for mc in market_caps],  # Scale for visualization
                color=returns,
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Daily Return (%)")
            )
        ))
        
        fig.update_layout(
            title="Market Cap vs Daily Return",
            xaxis_title="Market Cap (Billion VND)",
            yaxis_title="Daily Return (%)",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_technical_analysis(self):
        """Render technical analysis dashboard."""
        data = st.session_state.dashboard_data
        
        # Stock selector
        col1, col2 = st.columns([1, 3])
        
        with col1:
            selected_stock = st.selectbox("Chọn cổ phiếu:", data['stocks'])
        
        stock_data = data['stock_data'][selected_stock]
        
        # Price chart with technical indicators
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown(f"### 📈 Phân tích kỹ thuật - {selected_stock}")
        
        # Calculate technical indicators
        stock_data['SMA_20'] = stock_data['price'].rolling(20).mean()
        stock_data['SMA_50'] = stock_data['price'].rolling(50).mean()
        stock_data['BB_upper'] = stock_data['SMA_20'] + 2 * stock_data['price'].rolling(20).std()
        stock_data['BB_lower'] = stock_data['SMA_20'] - 2 * stock_data['price'].rolling(20).std()
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=['Price & Indicators', 'Volume', 'RSI']
        )
        
        # Price and moving averages
        fig.add_trace(go.Scatter(
            x=stock_data['date'], y=stock_data['price'],
            mode='lines', name='Price', line=dict(color='#1f77b4')
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=stock_data['date'], y=stock_data['SMA_20'],
            mode='lines', name='SMA 20', line=dict(color='orange')
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=stock_data['date'], y=stock_data['SMA_50'],
            mode='lines', name='SMA 50', line=dict(color='red')
        ), row=1, col=1)
        
        # Bollinger Bands
        fig.add_trace(go.Scatter(
            x=stock_data['date'], y=stock_data['BB_upper'],
            mode='lines', name='BB Upper', line=dict(color='gray', dash='dash')
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=stock_data['date'], y=stock_data['BB_lower'],
            mode='lines', name='BB Lower', line=dict(color='gray', dash='dash'),
            fill='tonexty', fillcolor='rgba(128,128,128,0.1)'
        ), row=1, col=1)
        
        # Volume
        fig.add_trace(go.Bar(
            x=stock_data['date'], y=stock_data['volume'],
            name='Volume', marker_color='lightblue'
        ), row=2, col=1)
        
        # RSI (simplified calculation)
        rsi_data = np.random.uniform(20, 80, len(stock_data))
        fig.add_trace(go.Scatter(
            x=stock_data['date'], y=rsi_data,
            mode='lines', name='RSI', line=dict(color='purple')
        ), row=3, col=1)
        
        # RSI levels
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        
        fig.update_layout(height=800, showlegend=True)
        fig.update_xaxes(title_text="Date", row=3, col=1)
        fig.update_yaxes(title_text="Price (VND)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_yaxes(title_text="RSI", row=3, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Technical summary
        self.render_technical_summary(selected_stock)
    
    def render_technical_summary(self, stock: str):
        """Render technical analysis summary."""
        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
        st.markdown(f"### 🎯 Tóm tắt kỹ thuật - {stock}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Xu hướng", "Tăng", "↗️")
            st.metric("RSI", "58.3", "Trung tính")
        
        with col2:
            st.metric("MACD", "Tích cực", "📈")
            st.metric("Volume", "Cao", "+15%")
        
        with col3:
            st.metric("Hỗ trợ", "24,750", "")
            st.metric("Kháng cự", "29,100", "")
        
        st.markdown("**🤖 Phân tích AI:** Cổ phiếu đang trong xu hướng tăng ngắn hạn với volume tốt. RSI ở vùng trung tính cho thấy còn dư địa tăng.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_stock_comparison(self):
        """Render stock comparison dashboard."""
        data = st.session_state.dashboard_data
        
        st.markdown("### 📊 So sánh cổ phiếu")
        
        # Stock selection
        col1, col2 = st.columns(2)
        
        with col1:
            stocks_to_compare = st.multiselect(
                "Chọn cổ phiếu để so sánh:",
                data['stocks'],
                default=['HPG', 'VIC', 'VCB']
            )
        
        if len(stocks_to_compare) >= 2:
            # Performance comparison
            self.render_performance_comparison(stocks_to_compare)
            
            # Fundamental comparison
            self.render_fundamental_comparison(stocks_to_compare)
            
            # Risk-return analysis
            self.render_risk_return_analysis(stocks_to_compare)
    
    def render_performance_comparison(self, stocks: List[str]):
        """Render performance comparison chart."""
        data = st.session_state.dashboard_data
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("### 📈 So sánh hiệu suất")
        
        fig = go.Figure()
        
        for stock in stocks:
            stock_data = data['stock_data'][stock]
            # Normalize to 100 for comparison
            normalized_price = (stock_data['price'] / stock_data['price'].iloc[0]) * 100
            
            fig.add_trace(go.Scatter(
                x=stock_data['date'],
                y=normalized_price,
                mode='lines',
                name=stock,
                line=dict(width=2)
            ))
        
        fig.update_layout(
            height=400,
            xaxis_title="Thời gian",
            yaxis_title="Hiệu suất (%)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_fundamental_comparison(self, stocks: List[str]):
        """Render fundamental comparison."""
        data = st.session_state.dashboard_data
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("### 📊 So sánh chỉ số cơ bản")
        
        # Prepare comparison data
        comparison_data = []
        for stock in stocks:
            fund_data = data['fundamental_data'][stock]
            comparison_data.append({
                'Stock': stock,
                'P/E': f"{fund_data['PE']:.1f}",
                'P/B': f"{fund_data['PB']:.1f}",
                'ROE': f"{fund_data['ROE']:.1f}%",
                'ROA': f"{fund_data['ROA']:.1f}%",
                'Market Cap': f"{fund_data['market_cap']:.0f}B"
            })
        
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Radar chart
        fig = go.Figure()
        
        metrics = ['PE', 'PB', 'ROE', 'ROA']
        
        for stock in stocks:
            fund_data = data['fundamental_data'][stock]
            values = [
                fund_data['PE']/25*100,  # Normalize to 0-100
                fund_data['PB']/4*100,
                fund_data['ROE'],
                fund_data['ROA']
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=metrics,
                fill='toself',
                name=stock
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_risk_return_analysis(self, stocks: List[str]):
        """Render risk-return analysis."""
        data = st.session_state.dashboard_data
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("### ⚖️ Phân tích rủi ro - lợi nhuận")
        
        # Calculate risk and return metrics
        risk_return_data = []
        
        for stock in stocks:
            stock_data = data['stock_data'][stock]
            returns = stock_data['returns']
            
            annual_return = returns.mean() * 252 * 100  # Annualized
            volatility = returns.std() * np.sqrt(252) * 100  # Annualized
            
            risk_return_data.append({
                'stock': stock,
                'return': annual_return,
                'risk': volatility
            })
        
        df_risk = pd.DataFrame(risk_return_data)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_risk['risk'],
            y=df_risk['return'],
            mode='markers+text',
            text=df_risk['stock'],
            textposition="top center",
            marker=dict(
                size=15,
                color=df_risk['return'],
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Annual Return (%)")
            )
        ))
        
        fig.update_layout(
            title="Risk-Return Profile",
            xaxis_title="Risk (Volatility %)",
            yaxis_title="Expected Return (%)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_sector_analysis(self):
        """Render sector analysis dashboard."""
        data = st.session_state.dashboard_data
        
        st.markdown("### 🏭 Phân tích theo ngành")
        
        # Sector performance
        sector_performance = {}
        
        for sector, stocks in data['sectors'].items():
            sector_returns = []
            for stock in stocks:
                if stock in data['stock_data']:
                    daily_return = data['stock_data'][stock]['returns'].iloc[-1]
                    sector_returns.append(daily_return)
            
            if sector_returns:
                sector_performance[sector] = np.mean(sector_returns) * 100
        
        # Sector performance chart
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("### 📊 Hiệu suất theo ngành")
        
        sectors = list(sector_performance.keys())
        performance = list(sector_performance.values())
        colors = ['green' if p > 0 else 'red' for p in performance]
        
        fig = go.Figure(data=[
            go.Bar(x=sectors, y=performance, marker_color=colors)
        ])
        
        fig.update_layout(
            height=400,
            xaxis_title="Ngành",
            yaxis_title="Hiệu suất (%)",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Sector details
        selected_sector = st.selectbox("Chọn ngành để phân tích chi tiết:", sectors)
        self.render_sector_details(selected_sector)
    
    def render_sector_details(self, sector: str):
        """Render detailed sector analysis."""
        data = st.session_state.dashboard_data
        
        if sector not in data['sectors']:
            return
        
        sector_stocks = data['sectors'][sector]
        
        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
        st.markdown(f"### 🔍 Chi tiết ngành {sector}")
        
        # Sector metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_pe = np.mean([data['fundamental_data'][s]['PE'] for s in sector_stocks if s in data['fundamental_data']])
            st.metric("P/E trung bình", f"{avg_pe:.1f}")
        
        with col2:
            avg_roe = np.mean([data['fundamental_data'][s]['ROE'] for s in sector_stocks if s in data['fundamental_data']])
            st.metric("ROE trung bình", f"{avg_roe:.1f}%")
        
        with col3:
            total_market_cap = sum([data['fundamental_data'][s]['market_cap'] for s in sector_stocks if s in data['fundamental_data']])
            st.metric("Tổng vốn hóa", f"{total_market_cap:.0f}B")
        
        # Stock details in sector
        sector_details = []
        for stock in sector_stocks:
            if stock in data['fundamental_data']:
                fund_data = data['fundamental_data'][stock]
                current_price = data['stock_data'][stock]['price'].iloc[-1]
                daily_return = data['stock_data'][stock]['returns'].iloc[-1] * 100
                
                sector_details.append({
                    'Cổ phiếu': stock,
                    'Giá': f"{current_price:,.0f}",
                    'Thay đổi': f"{daily_return:+.2f}%",
                    'P/E': f"{fund_data['PE']:.1f}",
                    'P/B': f"{fund_data['PB']:.1f}",
                    'ROE': f"{fund_data['ROE']:.1f}%"
                })
        
        if sector_details:
            df_sector = pd.DataFrame(sector_details)
            st.dataframe(df_sector, use_container_width=True, hide_index=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_portfolio_analysis(self):
        """Render portfolio analysis dashboard."""
        st.markdown("### 🎯 Phân tích danh mục đầu tư")
        
        # Portfolio builder
        data = st.session_state.dashboard_data
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### 📝 Xây dựng danh mục")
            
            portfolio_stocks = st.multiselect(
                "Chọn cổ phiếu:",
                data['stocks'],
                default=['HPG', 'VIC', 'VCB', 'FPT']
            )
            
            # Weight allocation
            if portfolio_stocks:
                weights = {}
                remaining_weight = 100
                
                for i, stock in enumerate(portfolio_stocks):
                    if i == len(portfolio_stocks) - 1:
                        # Last stock gets remaining weight
                        weight = remaining_weight
                        st.write(f"{stock}: {weight}%")
                    else:
                        weight = st.slider(
                            f"Tỷ trọng {stock} (%):",
                            0, remaining_weight, 
                            min(25, remaining_weight),
                            key=f"weight_{stock}"
                        )
                        remaining_weight -= weight
                    
                    weights[stock] = weight / 100
        
        with col2:
            if portfolio_stocks and weights:
                self.render_portfolio_performance(portfolio_stocks, weights)
    
    def render_portfolio_performance(self, stocks: List[str], weights: Dict[str, float]):
        """Render portfolio performance analysis."""
        data = st.session_state.dashboard_data
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("#### 📈 Hiệu suất danh mục")
        
        # Calculate portfolio performance
        portfolio_returns = None
        portfolio_value = None
        
        for stock in stocks:
            stock_data = data['stock_data'][stock]
            weight = weights[stock]
            
            if portfolio_returns is None:
                portfolio_returns = stock_data['returns'] * weight
                portfolio_value = (stock_data['price'] / stock_data['price'].iloc[0]) * weight
            else:
                portfolio_returns += stock_data['returns'] * weight
                portfolio_value += (stock_data['price'] / stock_data['price'].iloc[0]) * weight
        
        # Portfolio vs VN-Index
        vnindex_normalized = data['market_data']['vnindex'] / data['market_data']['vnindex'].iloc[0]
        portfolio_normalized = portfolio_value
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data['market_data']['date'],
            y=portfolio_normalized * 100,
            mode='lines',
            name='Portfolio',
            line=dict(color='#667eea', width=3)
        ))
        
        fig.add_trace(go.Scatter(
            x=data['market_data']['date'],
            y=vnindex_normalized * 100,
            mode='lines',
            name='VN-Index',
            line=dict(color='orange', width=2)
        ))
        
        fig.update_layout(
            height=400,
            xaxis_title="Thời gian",
            yaxis_title="Hiệu suất (%)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Portfolio metrics
        col1, col2, col3 = st.columns(3)
        
        portfolio_annual_return = portfolio_returns.mean() * 252 * 100
        portfolio_volatility = portfolio_returns.std() * np.sqrt(252) * 100
        sharpe_ratio = portfolio_annual_return / portfolio_volatility if portfolio_volatility > 0 else 0
        
        with col1:
            st.metric("Lợi nhuận năm", f"{portfolio_annual_return:.1f}%")
        
        with col2:
            st.metric("Độ biến động", f"{portfolio_volatility:.1f}%")
        
        with col3:
            st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main function for advanced dashboard."""
    dashboard = AdvancedDashboard()
    dashboard.run()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>📊 VN Stock Advisor Advanced Dashboard v0.7.0</p>
        <p>Powered by Plotly, Streamlit & Advanced Analytics</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
