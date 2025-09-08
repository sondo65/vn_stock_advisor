#!/usr/bin/env python3
"""
Simple test for P/E Calculator
"""
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_pe_calculator_simple():
    """Simple test for P/E Calculator"""
    print("=== Simple P/E Calculator Test ===")
    
    try:
        from vn_stock_advisor.tools.pe_calculator import PECalculator
        print("✅ P/E Calculator imported successfully")
        
        calculator = PECalculator()
        print("✅ P/E Calculator initialized successfully")
        
        # Test basic functionality
        print("\nTesting basic functionality...")
        
        # Test with a simple symbol
        result = calculator.calculate_accurate_pe("MSB", use_diluted_eps=True)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Success! P/E: {result.get('pe_ratio', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Import/Initialization error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pe_calculator_simple()
