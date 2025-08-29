#!/usr/bin/env python3
"""
Test UI Integration for Optimized Scanner

Test script to verify that the optimized scanner system
is properly integrated into the Streamlit UI components.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root / "src"))

def test_streamlit_imports():
    """Test if Streamlit app can import optimized scanner components."""
    print("🧪 Testing Streamlit App Imports...")
    
    try:
        # Test main app imports
        print("   Testing main streamlit_app.py imports...")
        
        # Simulate the imports from streamlit_app.py
        from src.vn_stock_advisor.scanner import (
            LightweightStockScanner, 
            ScreeningEngine,
            PriorityRankingSystem,
            TokenOptimizer,
            quick_scan_and_rank,
            find_opportunities,
            get_analysis_priorities
        )
        print("   ✅ Main app scanner imports successful")
        
        # Test UI components
        print("   Testing optimized_scanner_ui.py...")
        import optimized_scanner_ui
        print("   ✅ UI components import successful")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_mobile_app_imports():
    """Test if mobile app can import scanner components."""
    print("\n🧪 Testing Mobile App Imports...")
    
    try:
        # Test mobile app imports (simulate)
        from src.vn_stock_advisor.scanner import (
            LightweightStockScanner,
            quick_scan_market,
            find_opportunities
        )
        print("   ✅ Mobile app scanner imports successful")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_scanner_functionality():
    """Test basic scanner functionality for UI."""
    print("\n🧪 Testing Scanner Functionality for UI...")
    
    try:
        # Test lightweight scanner
        from src.vn_stock_advisor.scanner.lightweight_scanner import LightweightStockScanner
        scanner = LightweightStockScanner(max_workers=1)
        print("   ✅ LightweightStockScanner initialized")
        
        # Test screening engine
        from src.vn_stock_advisor.scanner.screening_engine import ScreeningEngine
        engine = ScreeningEngine()
        print("   ✅ ScreeningEngine initialized")
        
        # Test priority ranking
        from src.vn_stock_advisor.scanner.priority_ranking import PriorityRankingSystem
        ranking = PriorityRankingSystem()
        print("   ✅ PriorityRankingSystem initialized")
        
        # Test token optimizer
        from src.vn_stock_advisor.scanner.token_optimizer import TokenOptimizer
        optimizer = TokenOptimizer()
        print("   ✅ TokenOptimizer initialized")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_ui_workflow_simulation():
    """Simulate UI workflow without actual API calls."""
    print("\n🧪 Testing UI Workflow Simulation...")
    
    try:
        # Create mock scan results
        from src.vn_stock_advisor.scanner.lightweight_scanner import LightweightScanResult
        from datetime import datetime
        
        mock_results = []
        test_data = [
            {"symbol": "VIC", "score": 7.8, "pb": 1.8, "rsi": 58, "rec": "BUY"},
            {"symbol": "VCB", "score": 8.2, "pb": 1.1, "rsi": 45, "rec": "BUY"},
            {"symbol": "FPT", "score": 6.9, "pb": 2.9, "rsi": 62, "rec": "WATCH"}
        ]
        
        for data in test_data:
            result = LightweightScanResult(
                symbol=data["symbol"],
                company_name=f"Company {data['symbol']}",
                industry="Technology",
                current_price=100000,
                pb_ratio=data["pb"],
                pe_ratio=15.0,
                market_cap=1000000,
                rsi=data["rsi"],
                macd_signal="positive",
                ma_trend="upward",
                volume_trend="increasing",
                value_score=data["score"] * 0.8,
                momentum_score=data["score"] * 1.1,
                overall_score=data["score"],
                recommendation=data["rec"],
                confidence=0.8,
                scan_time=datetime.now(),
                data_quality="good"
            )
            mock_results.append(result)
        
        print(f"   ✅ Created {len(mock_results)} mock scan results")
        
        # Test screening workflow
        from src.vn_stock_advisor.scanner import find_opportunities
        opportunities = find_opportunities(mock_results)
        print(f"   ✅ Screening found {len(opportunities)} opportunity categories")
        
        # Test ranking workflow  
        from src.vn_stock_advisor.scanner import get_analysis_priorities
        priorities = get_analysis_priorities(mock_results)
        print(f"   ✅ Ranking created {len(priorities)} priority levels")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error in workflow simulation: {e}")
        return False

def test_ui_data_formats():
    """Test data format compatibility between scanner and UI."""
    print("\n🧪 Testing UI Data Format Compatibility...")
    
    try:
        # Test that UI can handle scanner output formats
        from src.vn_stock_advisor.scanner.lightweight_scanner import LightweightScanResult
        from datetime import datetime
        
        # Create sample result
        sample_result = LightweightScanResult(
            symbol="TEST",
            company_name="Test Company",
            industry="Technology",
            current_price=50000,
            pb_ratio=1.5,
            pe_ratio=12.0,
            market_cap=500000,
            rsi=55.0,
            macd_signal="positive",
            ma_trend="upward", 
            volume_trend="increasing",
            value_score=7.5,
            momentum_score=8.0,
            overall_score=7.8,
            recommendation="BUY",
            confidence=0.85,
            scan_time=datetime.now(),
            data_quality="good"
        )
        
        # Test data extraction for UI tables
        ui_data = {
            'Symbol': sample_result.symbol,
            'Rec': sample_result.recommendation,
            'Score': f"{sample_result.overall_score:.1f}",
            'P/B': f"{sample_result.pb_ratio:.2f}",
            'RSI': f"{sample_result.rsi:.1f}",
            'Confidence': f"{sample_result.confidence:.0%}"
        }
        
        print("   ✅ Data format conversion successful")
        print(f"   Sample UI data: {ui_data}")
        
        # Test conversion to dict for screening
        dict_format = {
            "symbol": sample_result.symbol,
            "pb_ratio": sample_result.pb_ratio,
            "pe_ratio": sample_result.pe_ratio,
            "rsi": sample_result.rsi,
            "macd_signal": sample_result.macd_signal,
            "ma_trend": sample_result.ma_trend,
            "volume_trend": sample_result.volume_trend,
            "industry": sample_result.industry,
            "value_score": sample_result.value_score,
            "momentum_score": sample_result.momentum_score,
            "overall_score": sample_result.overall_score
        }
        
        print("   ✅ Dictionary conversion successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error in data format test: {e}")
        return False

def main():
    """Run all UI integration tests."""
    print("🚀 VN STOCK ADVISOR - UI INTEGRATION TESTS")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Streamlit App Imports", test_streamlit_imports),
        ("Mobile App Imports", test_mobile_app_imports),
        ("Scanner Functionality", test_scanner_functionality),
        ("UI Workflow Simulation", test_ui_workflow_simulation),
        ("UI Data Format Compatibility", test_ui_data_formats)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running {test_name}...")
        print("="*60)
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 UI INTEGRATION TEST SUMMARY")
    print("="*60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🏁 Result: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL UI INTEGRATION TESTS PASSED!")
        print("✅ Optimized scanner is ready for UI deployment!")
        
        print("\n💡 Next Steps:")
        print("1. Run streamlit app: streamlit run streamlit_app.py")
        print("2. Test '⚡ Quét Nhanh' tab in the scanner section")
        print("3. Try mobile version: streamlit run mobile_app.py")
        print("4. Verify token optimization and caching")
        
        print("\n📱 UI Features Available:")
        print("• ⚡ Lightweight scanning with real-time progress")
        print("• 🎯 Multi-criteria screening interface")
        print("• 📊 Priority ranking with action buttons")
        print("• 📱 Mobile-optimized scanner with presets")
        print("• 💰 Token usage tracking and optimization")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    return passed == len(results)

if __name__ == "__main__":
    from datetime import datetime
    success = main()
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sys.exit(0 if success else 1)
