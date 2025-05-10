from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from vnstock import Vnstock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def tech_data_tool(symbol: str) -> str:
    """Lấy dữ liệu cổ phiếu phục vụ phân tích kĩ thuật."""
    try:
        # Initialize vnstock and get historical price data
        stock = Vnstock().stock(symbol=symbol, source="TCBS")
        
        # Get price data for the last 200 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=200)
        price_data = stock.quote.history(
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            interval="1D"  # Daily data
        )
        
        if price_data.empty:
            return f"Không tìm thấy dữ liệu lịch sử cho cổ phiếu {symbol}"
        
        # Calculate technical indicators
        tech_data = calculate_indicators(price_data)
        
        # Identify support and resistance levels
        support_resistance = find_support_resistance(price_data)
        
        # Get current price
        current_price = price_data['close'].iloc[-1]
        
        # Format result
        latest_indicators = tech_data.iloc[-1]
        
        result = f"""Mã cổ phiếu: {symbol}
        Giá hiện tại: {current_price:,.2f} VND
        
        CHỈ SỐ KỸ THUẬT (cập nhật mới nhất):
        - SMA (20): {latest_indicators['SMA_20']:,.2f}
        - SMA (50): {latest_indicators['SMA_50']:,.2f}
        - SMA (200): {latest_indicators['SMA_200']:,.2f}
        - EMA (12): {latest_indicators['EMA_12']:,.2f}
        - EMA (26): {latest_indicators['EMA_26']:,.2f}
        
        - RSI (14): {latest_indicators['RSI_14']:.2f}
        - MACD: {latest_indicators['MACD']:.2f}
        - MACD Signal: {latest_indicators['MACD_Signal']:.2f}
        - MACD Histogram: {latest_indicators['MACD_Hist']:.2f}
        
        - Bollinger Upper: {latest_indicators['BB_Upper']:,.2f}
        - Bollinger Middle: {latest_indicators['BB_Middle']:,.2f}
        - Bollinger Lower: {latest_indicators['BB_Lower']:,.2f}
        
        VÙNG HỖ TRỢ VÀ KHÁNG CỰ:
        {support_resistance}
        
        NHẬN ĐỊNH KỸ THUẬT:
        {get_technical_analysis(latest_indicators, current_price, support_resistance)}
        """
        
        return result
        
    except Exception as e:
        return f"Lỗi khi lấy dữ liệu kỹ thuật: {e}"

def calculate_indicators(df):
    """Calculate various technical indicators."""
    # Make a copy to avoid modifying original data
    data = df.copy()
    
    # Simple Moving Averages
    data['SMA_20'] = data['close'].rolling(window=20).mean()
    data['SMA_50'] = data['close'].rolling(window=50).mean()
    data['SMA_200'] = data['close'].rolling(window=200).mean()
    
    # Exponential Moving Averages
    data['EMA_12'] = data['close'].ewm(span=12, adjust=False).mean()
    data['EMA_26'] = data['close'].ewm(span=26, adjust=False).mean()
    
    # MACD
    data['MACD'] = data['EMA_12'] - data['EMA_26']
    data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['MACD_Hist'] = data['MACD'] - data['MACD_Signal']
    
    # RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    
    # Avoid division by zero
    rs = gain / loss.replace(0, np.nan)
    data['RSI_14'] = 100 - (100 / (1 + rs))
    data['RSI_14'] = data['RSI_14'].fillna(50)  # Fill NaN values with neutral RSI
    
    # Bollinger Bands
    data['BB_Middle'] = data['close'].rolling(window=20).mean()
    std_dev = data['close'].rolling(window=20).std()
    data['BB_Upper'] = data['BB_Middle'] + (std_dev * 2)
    data['BB_Lower'] = data['BB_Middle'] - (std_dev * 2)
    
    # Calculate ADX (Average Directional Index)
    high_diff = data['high'].diff()
    low_diff = data['low'].diff().multiply(-1)
    
    # True Range
    tr1 = data['high'] - data['low']
    tr2 = abs(data['high'] - data['close'].shift())
    tr3 = abs(data['low'] - data['close'].shift())
    data['TR'] = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
    data['ATR_14'] = data['TR'].rolling(window=14).mean()
    
    return data

def find_support_resistance(df, window=10, threshold=0.03):
    """Find support and resistance levels."""
    data = df.copy()
    
    # Find potential pivot points
    data['local_max'] = data['high'].rolling(window=window, center=True).apply(
        lambda x: x.iloc[len(x)//2] == max(x), raw=False
    )
    data['local_min'] = data['low'].rolling(window=window, center=True).apply(
        lambda x: x.iloc[len(x)//2] == min(x), raw=False
    )
    
    # Get pivot high/low points
    resistance_levels = data[data['local_max'] == 1]['high'].values
    support_levels = data[data['local_min'] == 1]['low'].values
    
    # Group close resistance/support levels
    current_price = data['close'].iloc[-1]
    
    # Function to cluster price levels
    def cluster_levels(levels, threshold_pct):
        if len(levels) == 0:
            return []
            
        levels = sorted(levels)
        clusters = [[levels[0]]]
        
        for level in levels[1:]:
            last_cluster = clusters[-1]
            last_value = last_cluster[-1]
            
            # If this level is within threshold% of the last value, add to the same cluster
            if abs((level - last_value) / last_value) < threshold_pct:
                last_cluster.append(level)
            else:
                clusters.append([level])
        
        # Calculate average for each cluster
        return [np.mean(cluster) for cluster in clusters]
    
    # Cluster and filter resistance levels
    resistance_levels = cluster_levels(resistance_levels, threshold)
    resistance_levels = [r for r in resistance_levels if r > current_price]
    resistance_levels = sorted(resistance_levels)[:3]  # Get nearest 3 levels
    
    # Cluster and filter support levels
    support_levels = cluster_levels(support_levels, threshold)
    support_levels = [s for s in support_levels if s < current_price]
    support_levels = sorted(support_levels, reverse=True)[:3]  # Get nearest 3 levels
    
    # Format result
    result = "Vùng kháng cự:\n"
    for i, level in enumerate(resistance_levels, 1):
        result += f"- R{i}: {level:,.2f} VND\n"
    
    result += "\nVùng hỗ trợ:\n"
    for i, level in enumerate(support_levels, 1):
        result += f"- S{i}: {level:,.2f} VND\n"
        
    return result

def get_technical_analysis(indicators, current_price, support_resistance):
    """Generate technical analysis text based on indicators."""
    analysis = []
    
    # Trend analysis based on SMAs
    if current_price > indicators['SMA_200'] and indicators['SMA_50'] > indicators['SMA_200']:
        analysis.append("- Xu hướng dài hạn: TĂNG (Giá trên SMA 200, SMA 50 trên SMA 200)")
    elif current_price < indicators['SMA_200'] and indicators['SMA_50'] < indicators['SMA_200']:
        analysis.append("- Xu hướng dài hạn: GIẢM (Giá dưới SMA 200, SMA 50 dưới SMA 200)")
    else:
        analysis.append("- Xu hướng dài hạn: TRUNG LẬP (Tín hiệu trái chiều giữa các SMA)")
    
    # Short-term trend
    if current_price > indicators['SMA_20'] and indicators['SMA_20'] > indicators['SMA_50']:
        analysis.append("- Xu hướng ngắn hạn: TĂNG (Giá trên SMA 20, SMA 20 trên SMA 50)")
    elif current_price < indicators['SMA_20'] and indicators['SMA_20'] < indicators['SMA_50']:
        analysis.append("- Xu hướng ngắn hạn: GIẢM (Giá dưới SMA 20, SMA 20 dưới SMA 50)")
    else:
        analysis.append("- Xu hướng ngắn hạn: TRUNG LẬP (Tín hiệu trái chiều giữa SMA ngắn hạn)")
    
    # RSI analysis
    if indicators['RSI_14'] > 70:
        analysis.append("- RSI: QUÁ MUA (RSI > 70), có khả năng điều chỉnh giảm")
    elif indicators['RSI_14'] < 30:
        analysis.append("- RSI: QUÁ BÁN (RSI < 30), có khả năng hồi phục")
    else:
        analysis.append(f"- RSI: TRUNG TÍNH ({indicators['RSI_14']:.2f})")
    
    # MACD analysis
    if indicators['MACD'] > indicators['MACD_Signal']:
        analysis.append("- MACD: TÍCH CỰC (MACD trên Signal Line)")
    else:
        analysis.append("- MACD: TIÊU CỰC (MACD dưới Signal Line)")
    
    # Bollinger Bands analysis
    if current_price > indicators['BB_Upper']:
        analysis.append("- Bollinger Bands: QUÁ MUA (Giá trên dải trên BB)")
    elif current_price < indicators['BB_Lower']:
        analysis.append("- Bollinger Bands: QUÁ BÁN (Giá dưới dải dưới BB)")
    else:
        position = (current_price - indicators['BB_Lower']) / (indicators['BB_Upper'] - indicators['BB_Lower'])
        if position > 0.8:
            analysis.append("- Bollinger Bands: GẦN VÙNG QUÁ MUA (Giá gần dải trên BB)")
        elif position < 0.2:
            analysis.append("- Bollinger Bands: GẦN VÙNG QUÁ BÁN (Giá gần dải dưới BB)")
        else:
            analysis.append("- Bollinger Bands: TRUNG TÍNH (Giá trong khoảng giữa dải BB)")
    
    return "\n".join(analysis)
    
def test_fund_data_tool():
    # Test with a valid stock symbol (e.g., VNM for Vinamilk)
    result = tech_data_tool("VNM")
    print("Test result for VNM:")
    print(result)
    
    # Test with an invalid symbol
    result = tech_data_tool("INVALID")
    print("\nTest result for invalid symbol:")
    print(result)

if __name__ == "__main__":
    test_fund_data_tool()