"""
Stock Scanner - Quét và phân tích nhiều mã cổ phiếu
"""
import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

from ..crew import VnStockAdvisor
from .ranking_system import RankingSystem


class StockScanner:
    """Quét và phân tích nhiều mã cổ phiếu đồng thời"""
    
    def __init__(self, max_workers: int = 3):
        """
        Initialize Stock Scanner
        
        Args:
            max_workers: Số lượng thread tối đa để phân tích đồng thời
        """
        self.max_workers = max_workers
        self.ranking_system = RankingSystem()
        self.results = []
        
    def get_vn30_stocks(self) -> List[str]:
        """Lấy danh sách mã cổ phiếu VN30"""
        return [
            'VIC', 'VHM', 'VRE', 'VCB', 'BID', 'CTG', 'TCB', 'MBB', 'ACB', 'TPB',
            'HPG', 'HSG', 'NKG', 'GVR', 'PLX', 'POW', 'GAS', 'VNM', 'MSN', 'MWG',
            'FPT', 'VJC', 'HVN', 'SAB', 'BVH', 'CTD', 'PDR', 'KDH', 'DXG', 'STB'
        ]
    
    def get_hnx30_stocks(self) -> List[str]:
        """Lấy danh sách mã cổ phiếu HNX30"""
        return [
            'SHB', 'PVS', 'CEO', 'TNG', 'VCS', 'IDC', 'NVB', 'PVB', 'THD', 'DTD',
            'MBS', 'BVS', 'PVC', 'VIG', 'NDN', 'VC3', 'PVI', 'TIG', 'VND', 'HUT',
            'LAS', 'VGS', 'NBC', 'SHS', 'VCG', 'DDG', 'PVD', 'SZC', 'VIG', 'API'
        ]
    
    def analyze_single_stock(self, symbol: str) -> Optional[Dict]:
        """
        Phân tích một mã cổ phiếu đơn lẻ
        
        Args:
            symbol: Mã cổ phiếu
            
        Returns:
            Dict chứa kết quả phân tích hoặc None nếu lỗi
        """
        try:
            print(f"🔍 Analyzing {symbol}...")
            
            # Tạo inputs cho CrewAI
            inputs = {
                "symbol": symbol,
                "current_date": str(datetime.now().date())
            }
            
            # Chạy phân tích (cần xử lý lỗi API key)
            try:
                advisor = VnStockAdvisor()
                result = advisor.crew().kickoff(inputs=inputs)
                
                # Parse kết quả JSON
                if hasattr(result, 'raw') and result.raw:
                    decision_data = json.loads(result.raw)
                    
                    # Tính điểm tổng hợp
                    total_score = self.ranking_system.calculate_total_score(decision_data)
                    
                    return {
                        'symbol': symbol,
                        'decision': decision_data.get('decision', 'N/A'),
                        'total_score': total_score,
                        'fund_score': decision_data.get('fund_reasoning', '').count('✅') * 2,
                        'tech_score': decision_data.get('tech_reasoning', '').count('✅') * 2,
                        'buy_price': decision_data.get('buy_price', 0),
                        'sell_price': decision_data.get('sell_price', 0),
                        'analysis_date': datetime.now().isoformat(),
                        'raw_data': decision_data
                    }
                else:
                    print(f"❌ No valid result for {symbol}")
                    return None
                    
            except Exception as e:
                print(f"❌ Analysis failed for {symbol}: {str(e)}")
                return None
                
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {str(e)}")
            return None
    
    def scan_stocks(self, 
                   stock_list: List[str], 
                   min_score: float = 7.5,
                   only_buy_recommendations: bool = True) -> List[Dict]:
        """
        Quét và phân tích danh sách cổ phiếu
        
        Args:
            stock_list: Danh sách mã cổ phiếu cần quét
            min_score: Điểm tối thiểu để lọc
            only_buy_recommendations: Chỉ lấy khuyến nghị MUA
            
        Returns:
            List các kết quả được sắp xếp theo điểm số giảm dần
        """
        print(f"🚀 Starting scan for {len(stock_list)} stocks...")
        print(f"📊 Filter: min_score={min_score}, only_buy={only_buy_recommendations}")
        
        results = []
        
        # Sử dụng ThreadPoolExecutor để phân tích đồng thời
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(self.analyze_single_stock, symbol): symbol 
                for symbol in stock_list
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result(timeout=300)  # 5 minutes timeout
                    if result:
                        results.append(result)
                        print(f"✅ {symbol}: {result['decision']} (Score: {result['total_score']:.1f})")
                    else:
                        print(f"⚠️ {symbol}: Analysis failed")
                except Exception as e:
                    print(f"❌ {symbol}: Exception - {str(e)}")
        
        # Lọc kết quả
        filtered_results = []
        for result in results:
            # Lọc theo điểm số
            if result['total_score'] < min_score:
                continue
                
            # Lọc chỉ khuyến nghị MUA
            if only_buy_recommendations and result['decision'].upper() != 'MUA':
                continue
                
            filtered_results.append(result)
        
        # Sắp xếp theo điểm số giảm dần
        filtered_results.sort(key=lambda x: x['total_score'], reverse=True)
        
        print(f"\n📈 SCAN COMPLETED:")
        print(f"   • Analyzed: {len(results)}/{len(stock_list)} stocks")
        print(f"   • Buy recommendations: {len(filtered_results)} stocks")
        
        return filtered_results
    
    def scan_vn30(self, **kwargs) -> List[Dict]:
        """Quét cổ phiếu VN30"""
        return self.scan_stocks(self.get_vn30_stocks(), **kwargs)
    
    def scan_hnx30(self, **kwargs) -> List[Dict]:
        """Quét cổ phiếu HNX30"""
        return self.scan_stocks(self.get_hnx30_stocks(), **kwargs)
    
    def export_results(self, results: List[Dict], filename: str = None) -> str:
        """
        Xuất kết quả ra file
        
        Args:
            results: Danh sách kết quả
            filename: Tên file (tự động tạo nếu None)
            
        Returns:
            Đường dẫn file đã xuất
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stock_scan_results_{timestamp}.json"
        
        # Chuẩn bị dữ liệu xuất
        export_data = {
            'scan_info': {
                'total_stocks': len(results),
                'scan_date': datetime.now().isoformat(),
                'min_score': 7.5,
                'only_buy_recommendations': True
            },
            'results': results
        }
        
        # Ghi file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"📁 Results exported to: {filename}")
        return filename
    
    def generate_summary_report(self, results: List[Dict]) -> str:
        """
        Tạo báo cáo tóm tắt
        
        Args:
            results: Danh sách kết quả
            
        Returns:
            Báo cáo dạng text
        """
        if not results:
            return "📊 STOCK SCAN SUMMARY\n❌ No stocks meet the criteria"
        
        report = []
        report.append("📊 STOCK SCAN SUMMARY")
        report.append("=" * 50)
        report.append(f"🗓️  Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"📈 Total Buy Recommendations: {len(results)}")
        report.append(f"⭐ Average Score: {sum(r['total_score'] for r in results) / len(results):.1f}")
        report.append("")
        
        report.append("🏆 TOP RECOMMENDATIONS:")
        report.append("-" * 30)
        
        for i, result in enumerate(results[:10], 1):  # Top 10
            report.append(f"{i:2d}. {result['symbol']:>4} | "
                         f"Score: {result['total_score']:5.1f} | "
                         f"Decision: {result['decision']:>4} | "
                         f"Buy: {result['buy_price']:>8,.0f} | "
                         f"Target: {result['sell_price']:>8,.0f}")
        
        if len(results) > 10:
            report.append(f"    ... and {len(results) - 10} more stocks")
        
        return "\n".join(report)


# Utility functions
def quick_scan_vn30(min_score: float = 7.5) -> List[Dict]:
    """
    Quick scan VN30 stocks
    
    Args:
        min_score: Minimum score threshold
        
    Returns:
        List of buy recommendations sorted by score
    """
    scanner = StockScanner(max_workers=2)  # Conservative for API limits
    return scanner.scan_vn30(min_score=min_score)


def quick_scan_custom(symbols: List[str], min_score: float = 7.5) -> List[Dict]:
    """
    Quick scan custom stock list
    
    Args:
        symbols: List of stock symbols
        min_score: Minimum score threshold
        
    Returns:
        List of buy recommendations sorted by score
    """
    scanner = StockScanner(max_workers=2)
    return scanner.scan_stocks(symbols, min_score=min_score)
