"""
Công cụ phân tích cơ bản chính xác sử dụng P/E Calculator
"""
from typing import Type, Optional, Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from vnstock import Vnstock
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Import P/E Calculator
try:
    from .pe_calculator import PECalculator
    PE_CALCULATOR_AVAILABLE = True
except ImportError:
    PE_CALCULATOR_AVAILABLE = False
    print("Warning: P/E Calculator not available")


class AccurateFundamentalInput(BaseModel):
    """Input schema for AccurateFundamentalTool."""
    symbol: str = Field(..., description="Mã cổ phiếu cần phân tích")


class AccurateFundamentalTool(BaseTool):
    """Công cụ phân tích cơ bản chính xác tránh thiên kiến dữ liệu"""
    
    name: str = "Công cụ phân tích cơ bản chính xác"
    description: str = "Công cụ phân tích cơ bản sử dụng P/E Calculator để tránh thiên kiến dữ liệu, cung cấp các chỉ số tài chính chính xác như P/E, P/B, ROE, ROA, EPS, D/E, biên lợi nhuận và EV/EBITDA."
    args_schema: Type[BaseModel] = AccurateFundamentalInput

    def _run(self, symbol: str) -> str:
        try:
            # Use real data with better error handling and caching
            import time
            import random
            
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            # Try multiple sources with proper error handling
            sources = ["VCI", "DNSE", "SSI"]
            stock = None
            company = None
            
            for source in sources:
                try:
                    print(f"Trying {source} for {symbol}...")
                    stock = Vnstock().stock(symbol=symbol, source=source)
                    company = Vnstock().stock(symbol=symbol, source=source).company
                    print(f"Successfully got data from {source}")
                    break
                except Exception as e:
                    print(f"Source {source} failed: {str(e)[:100]}...")
                    continue
            
            if stock is None:
                raise Exception("All data sources failed")
                
            financial_ratios = stock.finance.ratio(period="quarter")
            income_df = stock.finance.income_statement(period="quarter")

            # Get company full name & industry with error handling
            try:
                profile_data = company.profile().get("company_name")
                full_name = profile_data.iloc[0] if not profile_data.empty else f"Company {symbol}"
            except (IndexError, AttributeError):
                full_name = f"Company {symbol}"
            
            try:
                overview_data = company.overview().get("industry")
                industry = overview_data.iloc[0] if not overview_data.empty else "Unknown"
            except (IndexError, AttributeError):
                industry = "Unknown"

            # Get data from the latest row of DataFrame for financial ratios with error handling
            if financial_ratios.empty:
                return f"Không có dữ liệu tài chính cho cổ phiếu {symbol}"
            
            latest_ratios = financial_ratios.iloc[0]

            # Get last 4 quarters of income statement with error handling
            if income_df.empty:
                quarterly_trends = ["Không có dữ liệu báo cáo thu nhập"]
            else:
                last_4_quarters = income_df.head(4)
            
            # Extract financial ratios data - handle both TCBS and VCI formats
            try:
                # Try VCI format first (multi-level columns)
                pe_ratio = latest_ratios.get(('Chỉ tiêu định giá', 'P/E'), "N/A")
                pb_ratio = latest_ratios.get(('Chỉ tiêu định giá', 'P/B'), "N/A")
                roe = latest_ratios.get(('Chỉ tiêu khả năng sinh lợi', 'ROE (%)'), "N/A")
                roa = latest_ratios.get(('Chỉ tiêu khả năng sinh lợi', 'ROA (%)'), "N/A")
                eps = latest_ratios.get(('Chỉ tiêu định giá', 'EPS (VND)'), "N/A")
                de = latest_ratios.get(('Chỉ tiêu cơ cấu nguồn vốn', 'Debt/Equity'), "N/A")
                profit_margin = latest_ratios.get(('Chỉ tiêu khả năng sinh lợi', 'Gross Profit Margin (%)'), "N/A")
                evebitda = latest_ratios.get(('Chỉ tiêu định giá', 'EV/EBITDA'), "N/A")
            except:
                # Fallback to TCBS format
                pe_ratio = latest_ratios.get("price_to_earning", "N/A")
                pb_ratio = latest_ratios.get("price_to_book", "N/A")
                roe = latest_ratios.get("roe", "N/A")
                roa = latest_ratios.get("roa", "N/A")
                eps = latest_ratios.get("earning_per_share", "N/A")
                de = latest_ratios.get("debt_on_equity", "N/A")
                profit_margin = latest_ratios.get("gross_profit_margin", "N/A")
                evebitda = latest_ratios.get("value_before_ebitda", "N/A")
            
            # Calculate accurate P/E using P/E Calculator to avoid data bias
            accurate_pe_data = None
            bias_analysis = ""
            
            if PE_CALCULATOR_AVAILABLE:
                try:
                    pe_calculator = PECalculator()
                    accurate_pe_data = pe_calculator.calculate_accurate_pe(symbol, use_diluted_eps=True)
                    
                    # Use accurate P/E if available
                    if accurate_pe_data and "pe_ratio" in accurate_pe_data and accurate_pe_data["pe_ratio"]:
                        pe_ratio = accurate_pe_data["pe_ratio"]
                        eps = accurate_pe_data["eps_used"]
                        
                        # Add bias analysis
                        if "pe_difference" in accurate_pe_data and accurate_pe_data["pe_difference"]:
                            pe_difference = accurate_pe_data["pe_difference"]
                            if abs(pe_difference) > 0.5:
                                bias_analysis = f"""
            
            ⚠️ PHÂN TÍCH THIÊN KIẾN P/E:
            - P/E chính xác: {accurate_pe_data.get('pe_ratio', 'N/A')}
            - P/E từ nguồn: {accurate_pe_data.get('source_pe', 'N/A')}
            - Chênh lệch: {pe_difference:.2f}
            - Phương pháp: {accurate_pe_data.get('calculation_method', 'N/A')}
            - Cập nhật: {accurate_pe_data.get('last_updated', 'N/A')}
            
            📊 CHI TIẾT TÍNH TOÁN:
            - Lợi nhuận TTM: {accurate_pe_data.get('net_income_ttm', 'N/A'):,.0f} VND
            - Cổ phiếu lưu hành: {accurate_pe_data.get('shares_outstanding', 'N/A'):,.0f} cp
            - EPS Basic: {accurate_pe_data.get('eps_basic', 'N/A'):,.0f} VND
            - EPS Diluted: {accurate_pe_data.get('eps_diluted', 'N/A'):,.0f} VND
            - Giá hiện tại: {accurate_pe_data.get('current_price', 'N/A'):,.0f} VND
            """
                    
                    # Detect bias issues
                    bias_detection = pe_calculator.detect_pe_bias(symbol)
                    if "bias_detected" in bias_detection and bias_detection["bias_detected"]:
                        bias_analysis += f"""
            
            🚨 CÁC THIÊN KIẾN PHÁT HIỆN:
            {chr(10).join([f"- {bias}" for bias in bias_detection["bias_detected"]])}
            
            💡 KHUYẾN NGHỊ:
            {chr(10).join([f"- {rec}" for rec in bias_detection["recommendations"]])}
            """
                        
                except Exception as e:
                    print(f"Warning: Could not calculate accurate P/E: {e}")
                    bias_analysis = f"\n⚠️ Không thể tính P/E chính xác: {str(e)}"

            # Format quarterly income data only if we have data
            if 'last_4_quarters' in locals() and not last_4_quarters.empty:
                quarterly_trends = []
                for i, (_, quarter) in enumerate(last_4_quarters.iterrows()):
                    try:
                        # Detect and normalize units
                        # Revenue
                        revenue = quarter.get("Revenue (Bn. VND)", None)
                        if isinstance(revenue, (int, float)):
                            revenue_bn = revenue if revenue < 1e7 else revenue / 1e9
                            revenue_str = f"{revenue_bn:,.0f} tỉ đồng"
                        else:
                            revenue_str = "N/A"
                        # Gross Profit
                        gross_profit = quarter.get("Gross Profit", None)
                        if isinstance(gross_profit, (int, float)):
                            # Assume VND
                            gp_bn = gross_profit / 1e9 if gross_profit >= 1e7 else gross_profit
                            gross_profit_str = f"{gp_bn:,.0f} tỉ đồng" if gross_profit >= 1e7 else f"{gp_bn:,.0f} VND"
                        else:
                            gross_profit_str = "N/A"
                        # Net Profit For the Year
                        post_tax_profit = quarter.get("Net Profit For the Year", None)
                        if isinstance(post_tax_profit, (int, float)):
                            npty_bn = post_tax_profit / 1e9 if post_tax_profit >= 1e7 else post_tax_profit
                            post_tax_profit_str = f"{npty_bn:,.0f} tỉ đồng" if post_tax_profit >= 1e7 else f"{npty_bn:,.0f} VND"
                        else:
                            post_tax_profit_str = "N/A"

                        quarter_info = f"""
                        Quý T - {i + 1}:
                        - Doanh thu thuần: {revenue_str}
                        - Lợi nhuận gộp: {gross_profit_str}
                        - Lợi nhuận sau thuế: {post_tax_profit_str}
                        """
                        quarterly_trends.append(quarter_info)
                    except Exception:
                        quarterly_trends.append(f"Quý T - {i + 1}: Lỗi dữ liệu")
            else:
                quarterly_trends = ["Không có dữ liệu báo cáo thu nhập"]
            
            return f"""Mã cổ phiếu: {symbol}
            Tên công ty: {full_name}
            Ngành: {industry}
            Ngày phân tích: {datetime.now().strftime('%Y-%m-%d')}
            
            Tỷ lệ P/E: {pe_ratio}
            Tỷ lệ P/B: {pb_ratio}
            Tỷ lệ ROE: {roe}
            Tỷ lệ ROA: {roa}
            Biên lợi nhuận: {profit_margin}
            Lợi nhuận trên mỗi cổ phiếu EPS (VND): {eps}
            Hệ số nợ trên vốn chủ sở hữu D/E: {de}
            Tỷ lệ EV/EBITDA: {evebitda}
            {bias_analysis}

            XU HƯỚNG 4 QUÝ GẦN NHẤT:
            {"".join(quarterly_trends)}
            """
        except Exception as e:
            return f"Lỗi khi lấy dữ liệu: {e}"
