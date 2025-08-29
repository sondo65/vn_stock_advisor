"""
VN Stock Advisor - User Management & Export Features
Phase 4: User authentication, portfolio management, and export capabilities
"""

import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import json
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import yaml
from pathlib import Path
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.chart import LineChart, Reference

# Configuration
st.set_page_config(
    page_title="VN Stock Advisor - User Management",
    page_icon="👤",
    layout="wide"
)

# User management CSS
st.markdown("""
<style>
    .user-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .portfolio-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 5px solid #667eea;
    }
    
    .user-metric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .export-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .login-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

class UserManager:
    """User management and authentication system."""
    
    def __init__(self):
        """Initialize user manager."""
        self.users_file = Path("users.yaml")
        self.portfolios_file = Path("portfolios.json")
        self.init_user_data()
        self.init_authenticator()
    
    def init_user_data(self):
        """Initialize user data files."""
        # Default users
        default_users = {
            'usernames': {
                'demo': {
                    'name': 'Demo User',
                    'password': '$2b$12$xyz...demo',  # 'password123'
                    'email': 'demo@vnstockadvisor.com'
                },
                'investor1': {
                    'name': 'Nhà đầu tư 1',
                    'password': '$2b$12$xyz...investor',  # 'invest123'
                    'email': 'investor1@example.com'
                }
            }
        }
        
        if not self.users_file.exists():
            with open(self.users_file, 'w') as file:
                yaml.dump(default_users, file, default_flow_style=False)
        
        # Default portfolios
        default_portfolios = {
            'demo': {
                'stocks': ['HPG', 'VIC', 'VCB', 'FPT'],
                'weights': {'HPG': 0.3, 'VIC': 0.25, 'VCB': 0.25, 'FPT': 0.2},
                'created_date': datetime.now().isoformat(),
                'watchlist': ['MSN', 'TCB', 'SSI', 'GAS'],
                'analysis_history': []
            }
        }
        
        if not self.portfolios_file.exists():
            with open(self.portfolios_file, 'w') as file:
                json.dump(default_portfolios, file, indent=2)
    
    def init_authenticator(self):
        """Initialize Streamlit authenticator."""
        try:
            with open(self.users_file, 'r') as file:
                config = yaml.safe_load(file)
            
            self.authenticator = stauth.Authenticate(
                config['usernames'],
                'vnstock_advisor',  # cookie name
                'vnstock_key_2025',  # cookie key
                cookie_expiry_days=30
            )
        except Exception as e:
            st.error(f"Error initializing authenticator: {e}")
            self.authenticator = None
    
    def login(self):
        """Handle user login."""
        if not self.authenticator:
            st.error("Authentication system not available")
            return None, None, None
        
        try:
            name, authentication_status, username = self.authenticator.login('Login', 'main')
            
            if authentication_status == False:
                st.error('Username/password is incorrect')
            elif authentication_status == None:
                st.warning('Please enter your username and password')
            
            return name, authentication_status, username
            
        except Exception as e:
            st.error(f"Login error: {e}")
            return None, False, None
    
    def logout(self):
        """Handle user logout."""
        if self.authenticator:
            self.authenticator.logout('Logout', 'sidebar')
    
    def register_user(self):
        """Handle user registration."""
        if not self.authenticator:
            return
        
        try:
            if self.authenticator.register_user('Register user', preauthorization=False):
                st.success('User registered successfully')
                # Save updated users
                with open(self.users_file, 'w') as file:
                    yaml.dump(self.authenticator.credentials, file, default_flow_style=False)
        except Exception as e:
            st.error(f"Registration error: {e}")
    
    def reset_password(self):
        """Handle password reset."""
        if not self.authenticator:
            return
        
        try:
            username, email, new_random_password = self.authenticator.forgot_password('Forgot password')
            if username:
                st.success(f'New password sent to {email}: {new_random_password}')
                # Save updated users
                with open(self.users_file, 'w') as file:
                    yaml.dump(self.authenticator.credentials, file, default_flow_style=False)
        except Exception as e:
            st.error(f"Password reset error: {e}")
    
    def get_user_portfolio(self, username: str) -> Dict[str, Any]:
        """Get user portfolio data."""
        try:
            with open(self.portfolios_file, 'r') as file:
                portfolios = json.load(file)
            
            return portfolios.get(username, {
                'stocks': [],
                'weights': {},
                'created_date': datetime.now().isoformat(),
                'watchlist': [],
                'analysis_history': []
            })
        except Exception as e:
            st.error(f"Error loading portfolio: {e}")
            return {}
    
    def save_user_portfolio(self, username: str, portfolio: Dict[str, Any]):
        """Save user portfolio data."""
        try:
            with open(self.portfolios_file, 'r') as file:
                portfolios = json.load(file)
            
            portfolios[username] = portfolio
            
            with open(self.portfolios_file, 'w') as file:
                json.dump(portfolios, file, indent=2)
            
            st.success("Portfolio saved successfully!")
            
        except Exception as e:
            st.error(f"Error saving portfolio: {e}")

class ExportManager:
    """Export and reporting manager."""
    
    def __init__(self):
        """Initialize export manager."""
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom styles for PDF export."""
        custom_styles = {}
        
        # Title style
        custom_styles['CustomTitle'] = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#667eea'),
            alignment=1  # Center
        )
        
        # Subtitle style
        custom_styles['CustomSubtitle'] = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#764ba2')
        )
        
        return custom_styles
    
    def export_to_pdf(self, analysis_data: Dict[str, Any], filename: str = None) -> bytes:
        """Export analysis to PDF."""
        if not filename:
            filename = f"VN_Stock_Analysis_{analysis_data.get('symbol', 'Unknown')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph(
            f"VN Stock Advisor - Phân tích {analysis_data.get('symbol', 'Unknown')}",
            self.custom_styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Analysis info
        analysis_info = f"""
        <b>Mã cổ phiếu:</b> {analysis_data.get('symbol', 'N/A')}<br/>
        <b>Thời gian phân tích:</b> {analysis_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}<br/>
        <b>Khuyến nghị:</b> {analysis_data.get('recommendation', 'N/A')}<br/>
        <b>Độ tin cậy:</b> {analysis_data.get('confidence_score', 0)*100:.1f}%
        """
        
        info_para = Paragraph(analysis_info, self.styles['Normal'])
        story.append(info_para)
        story.append(Spacer(1, 20))
        
        # Fundamental analysis
        if 'fundamental_data' in analysis_data:
            story.append(Paragraph("Phân tích cơ bản", self.custom_styles['CustomSubtitle']))
            
            fund_text = analysis_data.get('fundamental_data', 'Không có dữ liệu')
            if isinstance(fund_text, dict):
                fund_text = self._format_dict_for_pdf(fund_text)
            
            fund_para = Paragraph(fund_text.replace('\n', '<br/>'), self.styles['Normal'])
            story.append(fund_para)
            story.append(Spacer(1, 15))
        
        # Technical analysis
        if 'technical_data' in analysis_data:
            story.append(Paragraph("Phân tích kỹ thuật", self.custom_styles['CustomSubtitle']))
            
            tech_text = analysis_data.get('technical_data', 'Không có dữ liệu')
            if isinstance(tech_text, dict):
                tech_text = self._format_dict_for_pdf(tech_text)
            
            tech_para = Paragraph(tech_text.replace('\n', '<br/>'), self.styles['Normal'])
            story.append(tech_para)
            story.append(Spacer(1, 15))
        
        # Price targets
        if 'price_targets' in analysis_data:
            story.append(Paragraph("Mục tiêu giá", self.custom_styles['CustomSubtitle']))
            
            targets = analysis_data['price_targets']
            if isinstance(targets, dict):
                target_data = [
                    ['Loại', 'Giá (VND)'],
                    ['Mua', f"{targets.get('buy_price', 0):,.0f}"],
                    ['Bán', f"{targets.get('sell_price', 0):,.0f}"],
                    ['Stop Loss', f"{targets.get('stop_loss', 0):,.0f}"]
                ]
                
                target_table = Table(target_data)
                target_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(target_table)
                story.append(Spacer(1, 15))
        
        # Footer
        footer = Paragraph(
            f"<i>Báo cáo được tạo bởi VN Stock Advisor v0.7.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
            self.styles['Normal']
        )
        story.append(Spacer(1, 30))
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def export_to_excel(self, analysis_data: Dict[str, Any], portfolio_data: Dict[str, Any] = None) -> bytes:
        """Export analysis and portfolio to Excel."""
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Analysis sheet
            if analysis_data:
                analysis_df = self._prepare_analysis_dataframe(analysis_data)
                analysis_df.to_excel(writer, sheet_name='Analysis', index=False)
                
                # Format analysis sheet
                worksheet = writer.sheets['Analysis']
                self._format_excel_sheet(worksheet, 'Analysis')
            
            # Portfolio sheet
            if portfolio_data:
                portfolio_df = self._prepare_portfolio_dataframe(portfolio_data)
                portfolio_df.to_excel(writer, sheet_name='Portfolio', index=False)
                
                # Format portfolio sheet
                worksheet = writer.sheets['Portfolio']
                self._format_excel_sheet(worksheet, 'Portfolio')
            
            # Summary sheet
            summary_data = {
                'Report Info': [
                    'VN Stock Advisor Export',
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"Version: 0.7.0",
                    f"Symbol: {analysis_data.get('symbol', 'N/A') if analysis_data else 'Portfolio Export'}"
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _format_dict_for_pdf(self, data: Dict[str, Any]) -> str:
        """Format dictionary data for PDF display."""
        formatted_lines = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                if key.upper() in ['PE', 'PB', 'ROE', 'ROA']:
                    formatted_lines.append(f"{key}: {value:.2f}")
                else:
                    formatted_lines.append(f"{key}: {value:,.0f}")
            else:
                formatted_lines.append(f"{key}: {value}")
        
        return '\n'.join(formatted_lines)
    
    def _prepare_analysis_dataframe(self, analysis_data: Dict[str, Any]) -> pd.DataFrame:
        """Prepare analysis data for Excel export."""
        data = {
            'Metric': [],
            'Value': []
        }
        
        # Basic info
        data['Metric'].extend(['Symbol', 'Timestamp', 'Recommendation', 'Confidence Score'])
        data['Value'].extend([
            analysis_data.get('symbol', 'N/A'),
            analysis_data.get('timestamp', 'N/A'),
            analysis_data.get('recommendation', 'N/A'),
            f"{analysis_data.get('confidence_score', 0)*100:.1f}%"
        ])
        
        # Fundamental data
        if 'fundamental_data' in analysis_data and isinstance(analysis_data['fundamental_data'], dict):
            for key, value in analysis_data['fundamental_data'].items():
                data['Metric'].append(f"Fund_{key}")
                data['Value'].append(value)
        
        # Technical data
        if 'technical_data' in analysis_data and isinstance(analysis_data['technical_data'], dict):
            for key, value in analysis_data['technical_data'].items():
                data['Metric'].append(f"Tech_{key}")
                data['Value'].append(value)
        
        return pd.DataFrame(data)
    
    def _prepare_portfolio_dataframe(self, portfolio_data: Dict[str, Any]) -> pd.DataFrame:
        """Prepare portfolio data for Excel export."""
        stocks = portfolio_data.get('stocks', [])
        weights = portfolio_data.get('weights', {})
        
        data = {
            'Stock': stocks,
            'Weight (%)': [weights.get(stock, 0) * 100 for stock in stocks],
            'Current Price': [25000 + hash(stock) % 50000 for stock in stocks],  # Demo prices
            'Daily Change (%)': [(hash(stock) % 10) - 5 for stock in stocks]  # Demo changes
        }
        
        return pd.DataFrame(data)
    
    def _format_excel_sheet(self, worksheet, sheet_type: str):
        """Format Excel worksheet."""
        # Header formatting
        header_fill = PatternFill(start_color='667eea', end_color='667eea', fill_type='solid')
        header_font = Font(color='FFFFFF', bold=True)
        
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

class UserManagementApp:
    """Main user management application."""
    
    def __init__(self):
        """Initialize user management app."""
        self.user_manager = UserManager()
        self.export_manager = ExportManager()
    
    def run(self):
        """Run user management application."""
        # Authentication
        name, authentication_status, username = self.user_manager.login()
        
        if authentication_status:
            # Logged in successfully
            self.render_authenticated_app(name, username)
        else:
            # Not logged in
            self.render_login_page()
    
    def render_login_page(self):
        """Render login page."""
        st.markdown("""
        <div class="user-header">
            <h1>👤 VN Stock Advisor</h1>
            <p>User Management & Portfolio System</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            
            tab1, tab2, tab3 = st.tabs(["🔑 Login", "📝 Register", "🔄 Reset Password"])
            
            with tab1:
                st.markdown("### Đăng nhập")
                st.info("Demo account: username='demo', password='password123'")
            
            with tab2:
                st.markdown("### Đăng ký tài khoản")
                self.user_manager.register_user()
            
            with tab3:
                st.markdown("### Quên mật khẩu")
                self.user_manager.reset_password()
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_authenticated_app(self, name: str, username: str):
        """Render authenticated user interface."""
        # Header
        st.markdown(f"""
        <div class="user-header">
            <h1>👋 Chào mừng, {name}!</h1>
            <p>VN Stock Advisor - Personal Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sidebar with logout
        with st.sidebar:
            st.markdown(f"### 👤 {name}")
            st.markdown(f"Username: `{username}`")
            
            if st.button("🚪 Logout"):
                self.user_manager.logout()
                st.experimental_rerun()
        
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Portfolio", "📈 Analysis", "📤 Export", "⚙️ Settings"
        ])
        
        with tab1:
            self.render_portfolio_tab(username)
        
        with tab2:
            self.render_analysis_tab(username)
        
        with tab3:
            self.render_export_tab(username)
        
        with tab4:
            self.render_settings_tab(username)
    
    def render_portfolio_tab(self, username: str):
        """Render portfolio management tab."""
        st.markdown("### 📊 Quản lý danh mục đầu tư")
        
        # Load user portfolio
        portfolio = self.user_manager.get_user_portfolio(username)
        
        # Portfolio overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="user-metric">
                <h3>Tổng cổ phiếu</h3>
                <h2>{}</h2>
            </div>
            """.format(len(portfolio.get('stocks', []))), unsafe_allow_html=True)
        
        with col2:
            total_value = sum([25000 + hash(stock) % 50000 for stock in portfolio.get('stocks', [])])
            st.markdown(f"""
            <div class="user-metric">
                <h3>Giá trị danh mục</h3>
                <h2>{total_value:,.0f}</h2>
                <p>VND</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            watchlist_count = len(portfolio.get('watchlist', []))
            st.markdown(f"""
            <div class="user-metric">
                <h3>Watchlist</h3>
                <h2>{watchlist_count}</h2>
                <p>Cổ phiếu</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            analysis_count = len(portfolio.get('analysis_history', []))
            st.markdown(f"""
            <div class="user-metric">
                <h3>Phân tích</h3>
                <h2>{analysis_count}</h2>
                <p>Lần</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Portfolio composition
        if portfolio.get('stocks'):
            self.render_portfolio_composition(portfolio)
        
        # Portfolio editor
        self.render_portfolio_editor(username, portfolio)
    
    def render_portfolio_composition(self, portfolio: Dict[str, Any]):
        """Render portfolio composition chart."""
        st.markdown('<div class="portfolio-card">', unsafe_allow_html=True)
        st.markdown("### 🥧 Cơ cấu danh mục")
        
        stocks = portfolio.get('stocks', [])
        weights = portfolio.get('weights', {})
        
        if stocks and weights:
            # Pie chart
            fig = go.Figure(data=[go.Pie(
                labels=stocks,
                values=[weights.get(stock, 0) * 100 for stock in stocks],
                hole=.3
            )])
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(
                title="Portfolio Allocation",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_portfolio_editor(self, username: str, portfolio: Dict[str, Any]):
        """Render portfolio editor."""
        st.markdown('<div class="portfolio-card">', unsafe_allow_html=True)
        st.markdown("### ✏️ Chỉnh sửa danh mục")
        
        # Stock selection
        available_stocks = ['HPG', 'VIC', 'VCB', 'FPT', 'MSN', 'TCB', 'VHM', 'SSI', 'GAS', 'CTG']
        
        selected_stocks = st.multiselect(
            "Chọn cổ phiếu:",
            available_stocks,
            default=portfolio.get('stocks', [])
        )
        
        # Weight allocation
        weights = {}
        if selected_stocks:
            st.markdown("**Phân bổ tỷ trọng:**")
            
            remaining_weight = 100
            for i, stock in enumerate(selected_stocks):
                if i == len(selected_stocks) - 1:
                    # Last stock gets remaining weight
                    weight = remaining_weight
                    st.write(f"{stock}: {weight}%")
                else:
                    current_weight = portfolio.get('weights', {}).get(stock, 0) * 100
                    weight = st.slider(
                        f"{stock} (%):",
                        0, remaining_weight,
                        min(int(current_weight), remaining_weight),
                        key=f"weight_{stock}_{username}"
                    )
                    remaining_weight -= weight
                
                weights[stock] = weight / 100
        
        # Watchlist
        watchlist = st.multiselect(
            "Danh sách theo dõi:",
            [s for s in available_stocks if s not in selected_stocks],
            default=portfolio.get('watchlist', [])
        )
        
        # Save portfolio
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Lưu danh mục", type="primary"):
                updated_portfolio = {
                    'stocks': selected_stocks,
                    'weights': weights,
                    'created_date': portfolio.get('created_date', datetime.now().isoformat()),
                    'updated_date': datetime.now().isoformat(),
                    'watchlist': watchlist,
                    'analysis_history': portfolio.get('analysis_history', [])
                }
                
                self.user_manager.save_user_portfolio(username, updated_portfolio)
                st.experimental_rerun()
        
        with col2:
            if st.button("🔄 Reset danh mục"):
                # Reset to default
                default_portfolio = {
                    'stocks': ['HPG', 'VIC', 'VCB'],
                    'weights': {'HPG': 0.4, 'VIC': 0.3, 'VCB': 0.3},
                    'created_date': datetime.now().isoformat(),
                    'watchlist': ['FPT', 'MSN'],
                    'analysis_history': []
                }
                
                self.user_manager.save_user_portfolio(username, default_portfolio)
                st.experimental_rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_analysis_tab(self, username: str):
        """Render analysis tab."""
        st.markdown("### 📈 Phân tích cổ phiếu")
        
        # Load portfolio for quick analysis
        portfolio = self.user_manager.get_user_portfolio(username)
        portfolio_stocks = portfolio.get('stocks', [])
        
        if portfolio_stocks:
            st.markdown("#### 🚀 Phân tích nhanh danh mục")
            
            col1, col2 = st.columns(2)
            
            with col1:
                selected_stock = st.selectbox("Chọn cổ phiếu từ danh mục:", portfolio_stocks)
            
            with col2:
                if st.button("📊 Phân tích", type="primary"):
                    # Run analysis (demo)
                    self.run_stock_analysis(username, selected_stock)
        
        # Analysis history
        self.render_analysis_history(username)
    
    def run_stock_analysis(self, username: str, symbol: str):
        """Run stock analysis and save to history."""
        with st.spinner(f"Đang phân tích {symbol}..."):
            # Demo analysis
            analysis_result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'recommendation': 'GIỮ',
                'confidence_score': 0.75,
                'fundamental_data': {
                    'PE': 15.3,
                    'PB': 1.7,
                    'ROE': 11.7,
                    'EPS': 1750
                },
                'technical_data': {
                    'RSI': 58.3,
                    'MACD': 'positive',
                    'trend': 'upward'
                },
                'price_targets': {
                    'buy_price': 24750,
                    'sell_price': 29100,
                    'stop_loss': 22000
                }
            }
            
            # Save to user's analysis history
            portfolio = self.user_manager.get_user_portfolio(username)
            if 'analysis_history' not in portfolio:
                portfolio['analysis_history'] = []
            
            portfolio['analysis_history'].append(analysis_result)
            self.user_manager.save_user_portfolio(username, portfolio)
            
            st.success(f"✅ Hoàn thành phân tích {symbol}!")
            
            # Display results
            self.display_analysis_result(analysis_result)
    
    def display_analysis_result(self, analysis: Dict[str, Any]):
        """Display analysis result."""
        st.markdown('<div class="portfolio-card">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Khuyến nghị", analysis['recommendation'])
        
        with col2:
            st.metric("Độ tin cậy", f"{analysis['confidence_score']*100:.0f}%")
        
        with col3:
            st.metric("Giá mua", f"{analysis['price_targets']['buy_price']:,.0f}")
        
        # Detailed results
        with st.expander("Chi tiết phân tích"):
            st.json(analysis)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_analysis_history(self, username: str):
        """Render analysis history."""
        st.markdown("#### 📚 Lịch sử phân tích")
        
        portfolio = self.user_manager.get_user_portfolio(username)
        history = portfolio.get('analysis_history', [])
        
        if history:
            # Convert to DataFrame for display
            df_data = []
            for analysis in reversed(history[-10:]):  # Last 10 analyses
                df_data.append({
                    'Thời gian': analysis['timestamp'][:16],
                    'Mã CK': analysis['symbol'],
                    'Khuyến nghị': analysis['recommendation'],
                    'Độ tin cậy': f"{analysis['confidence_score']*100:.0f}%",
                    'Giá mua': f"{analysis['price_targets']['buy_price']:,.0f}"
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Chưa có lịch sử phân tích. Hãy thử phân tích một cổ phiếu!")
    
    def render_export_tab(self, username: str):
        """Render export tab."""
        st.markdown("### 📤 Xuất báo cáo")
        
        portfolio = self.user_manager.get_user_portfolio(username)
        history = portfolio.get('analysis_history', [])
        
        st.markdown('<div class="export-section">', unsafe_allow_html=True)
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Xuất danh mục")
            
            export_format = st.selectbox("Định dạng:", ["Excel", "PDF", "JSON"])
            include_charts = st.checkbox("Bao gồm biểu đồ", value=True)
            
            if st.button("📥 Xuất danh mục", type="primary"):
                self.export_portfolio(username, portfolio, export_format, include_charts)
        
        with col2:
            st.markdown("#### 📈 Xuất phân tích")
            
            if history:
                selected_analysis = st.selectbox(
                    "Chọn phân tích:",
                    range(len(history)),
                    format_func=lambda x: f"{history[x]['symbol']} - {history[x]['timestamp'][:16]}"
                )
                
                analysis_format = st.selectbox("Định dạng:", ["PDF", "Excel", "JSON"], key="analysis_format")
                
                if st.button("📥 Xuất phân tích", type="primary"):
                    self.export_analysis(history[selected_analysis], analysis_format)
            else:
                st.info("Chưa có phân tích để xuất.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def export_portfolio(self, username: str, portfolio: Dict[str, Any], format_type: str, include_charts: bool):
        """Export user portfolio."""
        try:
            if format_type == "Excel":
                excel_data = self.export_manager.export_to_excel(None, portfolio)
                
                st.download_button(
                    label="📊 Tải xuống Excel",
                    data=excel_data,
                    file_name=f"Portfolio_{username}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            elif format_type == "JSON":
                json_data = json.dumps(portfolio, indent=2, ensure_ascii=False)
                
                st.download_button(
                    label="📄 Tải xuống JSON",
                    data=json_data,
                    file_name=f"Portfolio_{username}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
            
            elif format_type == "PDF":
                # Convert portfolio to analysis format for PDF
                portfolio_analysis = {
                    'symbol': 'PORTFOLIO',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'recommendation': 'PORTFOLIO_ANALYSIS',
                    'confidence_score': 1.0,
                    'fundamental_data': f"Stocks: {', '.join(portfolio.get('stocks', []))}",
                    'technical_data': f"Watchlist: {', '.join(portfolio.get('watchlist', []))}",
                    'price_targets': {'buy_price': 0, 'sell_price': 0}
                }
                
                pdf_data = self.export_manager.export_to_pdf(portfolio_analysis)
                
                st.download_button(
                    label="📄 Tải xuống PDF",
                    data=pdf_data,
                    file_name=f"Portfolio_{username}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )
            
            st.success(f"✅ Đã chuẩn bị file {format_type} để tải xuống!")
            
        except Exception as e:
            st.error(f"Lỗi khi xuất portfolio: {e}")
    
    def export_analysis(self, analysis: Dict[str, Any], format_type: str):
        """Export analysis result."""
        try:
            if format_type == "PDF":
                pdf_data = self.export_manager.export_to_pdf(analysis)
                
                st.download_button(
                    label="📄 Tải xuống PDF",
                    data=pdf_data,
                    file_name=f"Analysis_{analysis['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )
            
            elif format_type == "Excel":
                excel_data = self.export_manager.export_to_excel(analysis)
                
                st.download_button(
                    label="📊 Tải xuống Excel",
                    data=excel_data,
                    file_name=f"Analysis_{analysis['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            elif format_type == "JSON":
                json_data = json.dumps(analysis, indent=2, ensure_ascii=False)
                
                st.download_button(
                    label="📄 Tải xuống JSON",
                    data=json_data,
                    file_name=f"Analysis_{analysis['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
            
            st.success(f"✅ Đã chuẩn bị file {format_type} để tải xuống!")
            
        except Exception as e:
            st.error(f"Lỗi khi xuất phân tích: {e}")
    
    def render_settings_tab(self, username: str):
        """Render settings tab."""
        st.markdown("### ⚙️ Cài đặt tài khoản")
        
        # User preferences
        st.markdown('<div class="portfolio-card">', unsafe_allow_html=True)
        st.markdown("#### 🎨 Tùy chỉnh giao diện")
        
        theme = st.selectbox("Chủ đề:", ["Light", "Dark", "Auto"])
        language = st.selectbox("Ngôn ngữ:", ["Tiếng Việt", "English"])
        notifications = st.checkbox("Bật thông báo", value=True)
        
        if st.button("💾 Lưu cài đặt"):
            st.success("Đã lưu cài đặt!")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Account management
        st.markdown('<div class="portfolio-card">', unsafe_allow_html=True)
        st.markdown("#### 👤 Quản lý tài khoản")
        
        if st.button("🔑 Đổi mật khẩu"):
            st.info("Tính năng đổi mật khẩu sắp có!")
        
        if st.button("📧 Cập nhật email"):
            st.info("Tính năng cập nhật email sắp có!")
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main function for user management app."""
    try:
        app = UserManagementApp()
        app.run()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666;'>
            <p>👤 VN Stock Advisor User Management v0.7.0</p>
            <p>Secure • Personal • Professional</p>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Application error: {e}")
        st.info("Please check the installation and try again.")

if __name__ == "__main__":
    main()
