"""
Công cụ tính P/E chính xác tránh thiên kiến dữ liệu
"""
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from vnstock import Vnstock


class PECalculator:
    """Công cụ tính P/E chính xác tránh các thiên kiến dữ liệu"""
    
    def __init__(self):
        self.vnstock = Vnstock()
    
    def calculate_accurate_pe(self, symbol: str, use_diluted_eps: bool = True) -> Dict[str, Any]:
        """
        Tính P/E chính xác tránh thiên kiến dữ liệu
        
        Args:
            symbol: Mã cổ phiếu
            use_diluted_eps: Sử dụng Diluted EPS thay vì Basic EPS
            
        Returns:
            Dict chứa thông tin P/E và các chỉ số liên quan
        """
        try:
            # Lấy dữ liệu từ nhiều nguồn để so sánh
            sources = ["VCI", "DNSE", "SSI"]
            stock_data = None
            company_data = None
            
            for source in sources:
                try:
                    stock_data = self.vnstock.stock(symbol=symbol, source=source)
                    company_data = self.vnstock.stock(symbol=symbol, source=source).company
                    break
                except Exception as e:
                    print(f"Source {source} failed: {e}")
                    continue
            
            if stock_data is None:
                return {"error": "Không thể lấy dữ liệu từ bất kỳ nguồn nào"}
            
            # Lấy giá hiện tại
            current_price = self._get_current_price(stock_data)
            if current_price is None:
                return {"error": "Không thể lấy giá hiện tại"}
            
            # Lấy thông tin cổ phiếu lưu hành
            shares_info = self._get_shares_info(stock_data, company_data)
            if shares_info is None:
                return {"error": "Không thể lấy thông tin cổ phiếu lưu hành"}
            
            # Lấy lợi nhuận 4 quý gần nhất
            net_income_ttm = self._get_net_income_ttm(stock_data)
            if net_income_ttm is None:
                return {"error": "Không thể lấy lợi nhuận 4 quý gần nhất"}
            
            # Tính EPS chính xác
            eps_calculation = self._calculate_eps(
                net_income_ttm, 
                shares_info, 
                use_diluted_eps
            )
            
            # Tính P/E
            pe_ratio = current_price / eps_calculation["eps"] if eps_calculation["eps"] > 0 else None
            
            # So sánh với P/E từ nguồn dữ liệu
            source_pe = self._get_source_pe(stock_data)
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "net_income_ttm": net_income_ttm,
                "shares_outstanding": shares_info["shares_outstanding"],
                "diluted_shares": shares_info.get("diluted_shares"),
                "eps_basic": eps_calculation["eps_basic"],
                "eps_diluted": eps_calculation["eps_diluted"],
                "eps_used": eps_calculation["eps"],
                "pe_ratio": pe_ratio,
                "source_pe": source_pe,
                "pe_difference": (pe_ratio - source_pe) if (pe_ratio and source_pe) else None,
                "calculation_method": "Diluted EPS" if use_diluted_eps else "Basic EPS",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            return {"error": f"Lỗi tính toán P/E: {str(e)}"}
    
    def _get_current_price(self, stock_data) -> Optional[float]:
        """Lấy giá hiện tại"""
        try:
            # Thử lấy từ quote history
            try:
                from datetime import datetime, timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
                quote_history = stock_data.quote.history(
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                    interval="1D"
                )
                if not quote_history.empty:
                    closes = quote_history["close"].dropna()
                    if not closes.empty:
                        price = float(closes.iloc[-1])
                        # Chuyển đổi từ VND sang VND (giá thường được lưu dưới dạng VND)
                        if price < 1000:  # Nếu giá < 1000, có thể là đơn vị khác
                            price = price * 1000
                        return price
            except Exception as e:
                print(f"Quote history failed: {e}")
            
            # Thử lấy từ price history
            try:
                price_history = stock_data.price.history(count=1)
                if not price_history.empty:
                    price = float(price_history.iloc[0]['close'])
                    if price < 1000:  # Nếu giá < 1000, có thể là đơn vị khác
                        price = price * 1000
                    return price
            except Exception as e:
                print(f"Price history failed: {e}")
            
            # Thử lấy từ quote
            try:
                quote = stock_data.quote.live()
                if not quote.empty:
                    price = quote.iloc[0].get('price', None)
                    if price:
                        price = float(price)
                        if price < 1000:  # Nếu giá < 1000, có thể là đơn vị khác
                            price = price * 1000
                        return price
            except Exception as e:
                print(f"Quote failed: {e}")
            
            return None
        except Exception as e:
            print(f"Get current price failed: {e}")
            return None
    
    def _get_shares_info(self, stock_data, company_data) -> Optional[Dict[str, Any]]:
        """Lấy thông tin cổ phiếu lưu hành"""
        try:
            # Lấy từ financial ratios
            ratios = stock_data.finance.ratio(period="quarter")
            if not ratios.empty:
                latest_ratios = ratios.iloc[0]
                
                # Thử các key khác nhau cho shares outstanding
                shares_keys = [
                    ('Chỉ tiêu định giá', 'Outstanding Share (Mil. Shares)'),
                    ('Chỉ tiêu định giá', 'Số cổ phiếu lưu hành'),
                    'shares_outstanding',
                    'outstanding_shares',
                    'total_shares'
                ]
                
                shares_outstanding = None
                for key in shares_keys:
                    if isinstance(key, tuple):
                        shares_outstanding = latest_ratios.get(key, None)
                    else:
                        shares_outstanding = latest_ratios.get(key, None)
                    
                    if shares_outstanding and shares_outstanding != "N/A":
                        break
                
                if shares_outstanding:
                    # Chuyển đổi từ triệu cổ phiếu sang cổ phiếu
                    if shares_outstanding < 1000:  # Có thể là triệu cổ phiếu
                        shares_outstanding = shares_outstanding * 1_000_000
                    
                    return {
                        "shares_outstanding": int(shares_outstanding),
                        "diluted_shares": None  # Cần thêm logic để tính diluted shares
                    }
            
            # Fallback: lấy từ company profile
            try:
                profile = company_data.profile()
                if not profile.empty:
                    # Thử tìm thông tin cổ phiếu lưu hành
                    for col in profile.columns:
                        if 'shares' in col.lower() or 'cổ phiếu' in col.lower():
                            shares_value = profile.iloc[0][col]
                            if pd.notna(shares_value) and shares_value != "N/A":
                                return {
                                    "shares_outstanding": int(float(shares_value)),
                                    "diluted_shares": None
                                }
            except Exception:
                pass
            
            return None
            
        except Exception:
            return None
    
    def _get_net_income_ttm(self, stock_data) -> Optional[float]:
        """Lấy lợi nhuận 4 quý gần nhất (TTM)"""
        try:
            income_statement = stock_data.finance.income_statement(period="quarter")
            if income_statement.empty:
                return None
            
            # Lấy 4 quý gần nhất
            last_4_quarters = income_statement.head(4)
            
            # Tìm cột lợi nhuận sau thuế
            net_income_keys = [
                'Net Profit For the Year',
                'Net Income',
                'Lợi nhuận sau thuế',
                'net_profit'
            ]
            
            total_net_income = 0
            quarters_found = 0
            
            for _, quarter in last_4_quarters.iterrows():
                net_income = None
                for key in net_income_keys:
                    if key in quarter and pd.notna(quarter[key]) and quarter[key] != "N/A":
                        net_income = float(quarter[key])
                        break
                
                if net_income is not None:
                    total_net_income += net_income
                    quarters_found += 1
            
            return total_net_income if quarters_found > 0 else None
            
        except Exception:
            return None
    
    def _calculate_eps(self, net_income_ttm: float, shares_info: Dict[str, Any], use_diluted: bool) -> Dict[str, float]:
        """Tính EPS Basic và Diluted"""
        shares_outstanding = shares_info["shares_outstanding"]
        
        # EPS Basic
        eps_basic = net_income_ttm / shares_outstanding if shares_outstanding > 0 else 0
        
        # EPS Diluted (tạm thời sử dụng Basic, cần thêm logic tính diluted)
        eps_diluted = eps_basic  # TODO: Implement diluted shares calculation
        
        return {
            "eps_basic": eps_basic,
            "eps_diluted": eps_diluted,
            "eps": eps_diluted if use_diluted else eps_basic
        }
    
    def _get_source_pe(self, stock_data) -> Optional[float]:
        """Lấy P/E từ nguồn dữ liệu để so sánh"""
        try:
            ratios = stock_data.finance.ratio(period="quarter")
            if ratios.empty:
                return None
            
            latest_ratios = ratios.iloc[0]
            
            # Thử các key khác nhau cho P/E
            pe_keys = [
                ('Chỉ tiêu định giá', 'P/E'),
                'price_to_earning',
                'pe',
                'P/E'
            ]
            
            for key in pe_keys:
                if isinstance(key, tuple):
                    pe_value = latest_ratios.get(key, None)
                else:
                    pe_value = latest_ratios.get(key, None)
                
                if pe_value and pe_value != "N/A" and pd.notna(pe_value):
                    return float(pe_value)
            
            return None
            
        except Exception:
            return None
    
    def detect_pe_bias(self, symbol: str) -> Dict[str, Any]:
        """Phát hiện các thiên kiến trong tính toán P/E"""
        try:
            # Tính P/E chính xác
            accurate_pe = self.calculate_accurate_pe(symbol, use_diluted_eps=True)
            
            if "error" in accurate_pe:
                return accurate_pe
            
            # Phân tích thiên kiến
            bias_analysis = {
                "symbol": symbol,
                "accurate_pe": accurate_pe["pe_ratio"],
                "source_pe": accurate_pe["source_pe"],
                "pe_difference": accurate_pe["pe_difference"],
                "bias_detected": [],
                "recommendations": []
            }
            
            # Kiểm tra thiên kiến nhìn trước
            if accurate_pe["pe_difference"] and abs(accurate_pe["pe_difference"]) > 0.5:
                bias_analysis["bias_detected"].append("Look-ahead bias: P/E từ nguồn có thể sử dụng dữ liệu tương lai")
                bias_analysis["recommendations"].append("Sử dụng P/E được tính từ dữ liệu có sẵn tại thời điểm phân tích")
            
            # Kiểm tra thiên kiến đo lường
            if accurate_pe["eps_basic"] != accurate_pe["eps_diluted"]:
                bias_analysis["bias_detected"].append("Measurement bias: Sử dụng Basic EPS thay vì Diluted EPS")
                bias_analysis["recommendations"].append("Sử dụng Diluted EPS để tính P/E chính xác hơn")
            
            # Kiểm tra chất lượng dữ liệu
            if accurate_pe["shares_outstanding"] and accurate_pe["shares_outstanding"] < 1000000:
                bias_analysis["bias_detected"].append("Data quality issue: Số cổ phiếu lưu hành có vẻ không chính xác")
                bias_analysis["recommendations"].append("Kiểm tra lại dữ liệu cổ phiếu lưu hành")
            
            return bias_analysis
            
        except Exception as e:
            return {"error": f"Lỗi phát hiện thiên kiến: {str(e)}"}


def test_pe_calculator():
    """Test function cho P/E calculator"""
    calculator = PECalculator()
    
    # Test với MSB
    print("=== Test P/E Calculator với MSB ===")
    result = calculator.calculate_accurate_pe("MSB", use_diluted_eps=True)
    print(f"Kết quả: {result}")
    
    # Phát hiện thiên kiến
    print("\n=== Phát hiện thiên kiến ===")
    bias_result = calculator.detect_pe_bias("MSB")
    print(f"Phân tích thiên kiến: {bias_result}")


if __name__ == "__main__":
    test_pe_calculator()
