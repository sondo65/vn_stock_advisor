from vnstock import Vnstock

def fund_data_tool(symbol: str) -> str:
    """Lấy dữ liệu cổ phiếu phục vụ phân tích cơ bản."""
    try:
        # Initialize the class 
        stock = Vnstock().stock(symbol=symbol, source="TCBS")
        financial_ratios = stock.finance.ratio(period="quarter")
        income_df = stock.finance.income_statement(period="quarter")

        # Get data from the latest row of DataFrame for financial ratios
        latest_ratios = financial_ratios.iloc[0]

        # Get last 4 quarters of income statement
        last_4_quarters = income_df.head(4)
        
        # Extract financial ratios data
        pe_ratio = latest_ratios.get("price_to_earning", "N/A")
        pb_ratio = latest_ratios.get("price_to_book", "N/A")
        roe = latest_ratios.get("roe", "N/A")
        roa = latest_ratios.get("roa", "N/A")
        eps = latest_ratios.get("earning_per_share", "N/A")
        de = latest_ratios.get("debt_on_equity", "N/A")
        profit_margin = latest_ratios.get("gross_profit_margin", "N/A")
        evebitda = latest_ratios.get("value_before_ebitda", "N/A")

        # Format quarterly income data
        quarterly_trends = []
        for i, (_, quarter) in enumerate(last_4_quarters.iterrows()):
            quarter_num = 4 - i # Will give us Q4, Q3, Q2, Q1
            quarter_info = f"""
            Quý {quarter_num}:
            - Doanh thu thuần: {quarter.get("revenue", "N/A"):,.0f} VND
            - Lợi nhuận gộp: {quarter.get("gross_profit", "N/A"):,.0f} VND
            - Lợi nhuận sau thuế: {quarter.get("post_tax_profit", "N/A"):,.0f} VND
            """
            quarterly_trends.append(quarter_info)
        
        return f"""Mã cổ phiếu: {symbol}
        Tỷ lệ P/E: {pe_ratio}
        Tỷ lệ P/B: {pb_ratio}
        Tỷ lệ ROE: {roe}
        Tỷ lệ ROA: {roa}
        Biên lợi nhuận: {profit_margin}
        Lợi nhuận trên mỗi cổ phiếu EPS (VND): {eps}
        Hệ số nợ trên vốn chủ sở hữu D/E: {de}
        Tỷ lệ EV/EBITDA: {evebitda}

        XU HƯỚNG 4 QUÝ GẦN NHẤT:
        {''.join(quarterly_trends)}
        """
    except Exception as e:
        return f"Lỗi khi lấy dữ liệu: {e}"

def test_fund_data_tool():
    # Test with a valid stock symbol (e.g., VNM for Vinamilk)
    result = fund_data_tool("VNM")
    print("Test result for VNM:")
    print(result)
    
    # Test with an invalid symbol
    result = fund_data_tool("INVALID")
    print("\nTest result for invalid symbol:")
    print(result)

if __name__ == "__main__":
    test_fund_data_tool()