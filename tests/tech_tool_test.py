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
        
        # Get recent price and volume data
        current_price = price_data['close'].iloc[-1]
        recent_prices = price_data['close'].iloc[-5:-1]
        current_volume = price_data['volume'].iloc[-1]
        recent_volumes = price_data['volume'].iloc[-5:-1]
        
        # Format result
        latest_indicators = tech_data.iloc[-1]
        
        result = f"""Mã cổ phiếu: {symbol}
        Giá hiện tại: {current_price:,.2f} VND
        Khối lượng giao dịch: {current_volume:,.0f} cp

        GIÁ ĐÓNG CỬA GẦN NHẤT:
        - T-1: {recent_prices.iloc[-1]:,.2f} VND (KL: {recent_volumes.iloc[-1]:,.0f} cp)
        - T-2: {recent_prices.iloc[-2]:,.2f} VND (KL: {recent_volumes.iloc[-2]:,.0f} cp)
        - T-3: {recent_prices.iloc[-3]:,.2f} VND (KL: {recent_volumes.iloc[-3]:,.0f} cp)
        - T-4: {recent_prices.iloc[-4]:,.2f} VND (KL: {recent_volumes.iloc[-4]:,.0f} cp)
        
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

        CHỈ SỐ KHỐI LƯỢNG:
        - Khối lượng hiện tại: {current_volume:,.0f} cp
        - Trung bình 10 phiên: {latest_indicators['Volume_SMA_10']:,.0f} cp
        - Trung bình 20 phiên: {latest_indicators['Volume_SMA_20']:,.0f} cp
        - Trung bình 50 phiên: {latest_indicators['Volume_SMA_50']:,.0f} cp
        - Tỷ lệ KL/TB20: {latest_indicators['Volume_Ratio_20']:.2f}
        - On-Balance Volume (OBV): {latest_indicators['OBV']:,.0f}
        - Money Flow Index (MFI): {latest_indicators['MFI']:.2f}
        - Chaikin Money Flow (CMF): {latest_indicators['CMF']:.2f}
        
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
    
    # Calculate volume moving averages
    data['Volume_SMA_10'] = data['volume'].rolling(window=10).mean()
    data['Volume_SMA_20'] = data['volume'].rolling(window=20).mean()
    data['Volume_SMA_50'] = data['volume'].rolling(window=50).mean()
    
    # Calculate volume ratio compared to average
    data['Volume_Ratio_10'] = data['volume'] / data['Volume_SMA_10']
    data['Volume_Ratio_20'] = data['volume'] / data['Volume_SMA_20']
    
    # On-Balance Volume (OBV)
    data['OBV'] = 0
    data.loc[0, 'OBV'] = data.loc[0, 'volume']
    for i in range(1, len(data)):
        if data.loc[i, 'close'] > data.loc[i-1, 'close']:
            data.loc[i, 'OBV'] = data.loc[i-1, 'OBV'] + data.loc[i, 'volume']
        elif data.loc[i, 'close'] < data.loc[i-1, 'close']:
            data.loc[i, 'OBV'] = data.loc[i-1, 'OBV'] - data.loc[i, 'volume']
        else:
            data.loc[i, 'OBV'] = data.loc[i-1, 'OBV']

    # Money Flow Index (MFI)
    # Calculate typical price
    data['TypicalPrice'] = (data['high'] + data['low'] + data['close']) / 3
    
    # Calculate Raw Money Flow
    data['RawMoneyFlow'] = data['TypicalPrice'] * data['volume']
    
    # Calculate Positive and Negative Money Flow
    data['PositiveFlow'] = 0
    data['NegativeFlow'] = 0
    
    for i in range(1, len(data)):
        if data.loc[i, 'TypicalPrice'] > data.loc[i-1, 'TypicalPrice']:
            data.loc[i, 'PositiveFlow'] = data.loc[i, 'RawMoneyFlow']
        else:
            data.loc[i, 'NegativeFlow'] = data.loc[i, 'RawMoneyFlow']
    
    # Calculate 14-period Money Flow Ratio and MFI
    period = 14
    data['PositiveFlow14'] = data['PositiveFlow'].rolling(window=period).sum()
    data['NegativeFlow14'] = data['NegativeFlow'].rolling(window=period).sum()
    
    # Avoid division by zero
    data['MoneyFlowRatio'] = data['PositiveFlow14'] / data['NegativeFlow14'].replace(0, np.nan)
    data['MFI'] = 100 - (100 / (1 + data['MoneyFlowRatio']))
    data['MFI'] = data['MFI'].fillna(50)  # Fill NaN values with neutral MFI
    
    # Chaikin Money Flow (CMF)
    period = 20
    data['MoneyFlowMultiplier'] = ((data['close'] - data['low']) - (data['high'] - data['close'])) / (data['high'] - data['low'])
    data['MoneyFlowVolume'] = data['MoneyFlowMultiplier'] * data['volume']
    data['CMF'] = data['MoneyFlowVolume'].rolling(window=period).sum() / data['volume'].rolling(window=period).sum()
    
    # Find recent price-volume divergences
    data['Price_Up'] = data['close'] > data['close'].shift(1)
    data['Volume_Up'] = data['volume'] > data['volume'].shift(1)
    
    # Positive divergence: Price down but volume up (potential reversal)
    data['Positive_Divergence'] = (~data['Price_Up']) & data['Volume_Up']
    
    # Negative divergence: Price up but volume down (potential weakness)
    data['Negative_Divergence'] = data['Price_Up'] & (~data['Volume_Up'])

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

    # Volume ratio analysis
        volume_ratio_20 = indicators['Volume_Ratio_20']
        if volume_ratio_20 > 2.0:
            analysis.append("- Khối lượng: RẤT CAO (>200% trung bình 20 phiên)")
        elif volume_ratio_20 > 1.5:
            analysis.append("- Khối lượng: CAO (150-200% trung bình 20 phiên)")
        elif volume_ratio_20 < 0.5:
            analysis.append("- Khối lượng: THẤP (<50% trung bình 20 phiên)")
        else:
            analysis.append("- Khối lượng: BÌNH THƯỜNG (50-150% trung bình 20 phiên)")

        # Volume trend analysis
        if (indicators['Volume_SMA_10'] > indicators['Volume_SMA_20'] and 
            indicators['Volume_SMA_20'] > indicators['Volume_SMA_50']):
            analysis.append("- Xu hướng khối lượng: TĂNG (SMA 10 > SMA 20 > SMA 50)")
        elif (indicators['Volume_SMA_10'] < indicators['Volume_SMA_20'] and 
            indicators['Volume_SMA_20'] < indicators['Volume_SMA_50']):
            analysis.append("- Xu hướng khối lượng: GIẢM (SMA 10 < SMA 20 < SMA 50)")
        else:
            analysis.append("- Xu hướng khối lượng: TRUNG LẬP")

        # OBV trend analysis
        current_volume = indicators['volume']
        if current_volume > indicators['Volume_SMA_20'] * 1.5:
            if current_price > indicators['SMA_20']:
                analysis.append("- Tín hiệu khối lượng: TÍCH CỰC (Khối lượng cao kèm giá tăng)")
            else:
                analysis.append("- Tín hiệu khối lượng: TIÊU CỰC (Khối lượng cao kèm giá giảm)")
    
    # MFI confirmation
    if indicators['MFI'] > 80:
        analysis.append("- Dòng tiền: QUÁ MUA (MFI > 80)")
    elif indicators['MFI'] < 20:
        analysis.append("- Dòng tiền: QUÁ BÁN (MFI < 20)")
    
    # Combine volume and price signals
    if indicators['CMF'] > 0 and indicators['OBV'] > indicators.get('OBV_prev', 0) and current_price > indicators['SMA_20']:
        analysis.append("- Kết hợp giá-khối lượng: RẤT TÍCH CỰC (CMF+, OBV tăng, giá trên SMA20)")
    elif indicators['CMF'] < 0 and indicators['OBV'] < indicators.get('OBV_prev', 0) and current_price < indicators['SMA_20']:
        analysis.append("- Kết hợp giá-khối lượng: RẤT TIÊU CỰC (CMF-, OBV giảm, giá dưới SMA20)")
    
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