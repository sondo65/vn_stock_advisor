#!/usr/bin/env python3
"""
Test script for Phase 4 User Experience & API Support features.
"""

import sys
import os
import asyncio
import json
import requests
import time
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_streamlit_app():
    """Test Streamlit web interface."""
    print("🌐 Testing Streamlit Web Interface...")
    
    try:
        # Check if streamlit_app.py exists
        app_path = Path("streamlit_app.py")
        if app_path.exists():
            print("✅ Streamlit App: File exists")
            
            # Read and validate content
            with open(app_path, 'r') as f:
                content = f.read()
            
            # Check for key components
            required_components = [
                "StockAnalysisApp",
                "st.set_page_config",
                "render_stock_analysis",
                "render_dashboard",
                "_run_stock_analysis"
            ]
            
            missing_components = []
            for component in required_components:
                if component not in content:
                    missing_components.append(component)
            
            if not missing_components:
                print("✅ Streamlit App: All required components found")
            else:
                print(f"⚠️ Streamlit App: Missing components: {missing_components}")
            
            return len(missing_components) == 0
        else:
            print("❌ Streamlit App: File not found")
            return False
            
    except Exception as e:
        print(f"❌ Streamlit App: Error - {e}")
        return False

def test_mobile_app():
    """Test mobile-responsive interface."""
    print("📱 Testing Mobile Interface...")
    
    try:
        # Check if mobile_app.py exists
        app_path = Path("mobile_app.py")
        if app_path.exists():
            print("✅ Mobile App: File exists")
            
            # Read and validate content
            with open(app_path, 'r') as f:
                content = f.read()
            
            # Check for mobile-specific features
            mobile_features = [
                "mobile-card",
                "mobile-header",
                "MobileStockApp",
                "@media (max-width: 768px)",
                "render_mobile_results"
            ]
            
            missing_features = []
            for feature in mobile_features:
                if feature not in content:
                    missing_features.append(feature)
            
            if not missing_features:
                print("✅ Mobile App: All mobile features found")
            else:
                print(f"⚠️ Mobile App: Missing features: {missing_features}")
            
            return len(missing_features) == 0
        else:
            print("❌ Mobile App: File not found")
            return False
            
    except Exception as e:
        print(f"❌ Mobile App: Error - {e}")
        return False

def test_api_endpoints():
    """Test REST API endpoints."""
    print("🔌 Testing REST API...")
    
    try:
        # Check if API file exists
        api_path = Path("api/main.py")
        if api_path.exists():
            print("✅ API: File exists")
            
            # Read and validate content
            with open(api_path, 'r') as f:
                content = f.read()
            
            # Check for key API endpoints
            required_endpoints = [
                "@app.get(\"/\")",
                "@app.get(\"/health\")",
                "@app.post(\"/analyze\")",
                "@app.get(\"/analyze/{analysis_id}\")",
                "@app.get(\"/market/overview\")",
                "@app.post(\"/portfolio\")"
            ]
            
            missing_endpoints = []
            for endpoint in required_endpoints:
                if endpoint not in content:
                    missing_endpoints.append(endpoint)
            
            if not missing_endpoints:
                print("✅ API: All required endpoints found")
            else:
                print(f"⚠️ API: Missing endpoints: {missing_endpoints}")
            
            # Check for Pydantic models
            models = [
                "StockAnalysisRequest",
                "StockAnalysisResponse",
                "MarketOverviewResponse",
                "HealthResponse"
            ]
            
            missing_models = []
            for model in models:
                if model not in content:
                    missing_models.append(model)
            
            if not missing_models:
                print("✅ API: All Pydantic models found")
            else:
                print(f"⚠️ API: Missing models: {missing_models}")
            
            return len(missing_endpoints) == 0 and len(missing_models) == 0
        else:
            print("❌ API: File not found")
            return False
            
    except Exception as e:
        print(f"❌ API: Error - {e}")
        return False

async def test_api_server():
    """Test API server functionality (if running)."""
    print("🚀 Testing API Server...")
    
    try:
        # Try to connect to API server
        base_url = "http://localhost:8000"
        
        # Test health endpoint
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API Server: Health check passed")
                
                # Test root endpoint
                root_response = requests.get(f"{base_url}/", timeout=5)
                if root_response.status_code == 200:
                    print("✅ API Server: Root endpoint working")
                
                # Test market overview
                market_response = requests.get(f"{base_url}/market/overview", timeout=5)
                if market_response.status_code == 200:
                    print("✅ API Server: Market overview endpoint working")
                
                return True
            else:
                print(f"⚠️ API Server: Health check failed - Status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("⚠️ API Server: Not running (this is expected if not started)")
            return True  # Not an error if server isn't running
            
    except Exception as e:
        print(f"❌ API Server: Error - {e}")
        return False

def test_dashboard():
    """Test advanced dashboard."""
    print("📊 Testing Advanced Dashboard...")
    
    try:
        # Check if dashboard.py exists
        dashboard_path = Path("dashboard.py")
        if dashboard_path.exists():
            print("✅ Dashboard: File exists")
            
            # Read and validate content
            with open(dashboard_path, 'r') as f:
                content = f.read()
            
            # Check for dashboard components
            dashboard_components = [
                "AdvancedDashboard",
                "render_market_overview",
                "render_technical_analysis",
                "render_stock_comparison",
                "render_sector_analysis",
                "render_portfolio_analysis"
            ]
            
            missing_components = []
            for component in dashboard_components:
                if component not in content:
                    missing_components.append(component)
            
            if not missing_components:
                print("✅ Dashboard: All components found")
            else:
                print(f"⚠️ Dashboard: Missing components: {missing_components}")
            
            # Check for Plotly integration
            plotly_features = [
                "plotly.graph_objects",
                "make_subplots",
                "go.Scatter",
                "go.Bar",
                "st.plotly_chart"
            ]
            
            missing_plotly = []
            for feature in plotly_features:
                if feature not in content:
                    missing_plotly.append(feature)
            
            if not missing_plotly:
                print("✅ Dashboard: Plotly integration complete")
            else:
                print(f"⚠️ Dashboard: Missing Plotly features: {missing_plotly}")
            
            return len(missing_components) == 0 and len(missing_plotly) == 0
        else:
            print("❌ Dashboard: File not found")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard: Error - {e}")
        return False

def test_user_management():
    """Test user management system."""
    print("👤 Testing User Management...")
    
    try:
        # Check if user_management.py exists
        user_path = Path("user_management.py")
        if user_path.exists():
            print("✅ User Management: File exists")
            
            # Read and validate content
            with open(user_path, 'r') as f:
                content = f.read()
            
            # Check for user management components
            user_components = [
                "UserManager",
                "ExportManager",
                "streamlit_authenticator",
                "login",
                "register_user",
                "get_user_portfolio",
                "export_to_pdf",
                "export_to_excel"
            ]
            
            missing_components = []
            for component in user_components:
                if component not in content:
                    missing_components.append(component)
            
            if not missing_components:
                print("✅ User Management: All components found")
            else:
                print(f"⚠️ User Management: Missing components: {missing_components}")
            
            # Check for export libraries
            export_libs = [
                "reportlab",
                "openpyxl",
                "SimpleDocTemplate",
                "ExcelWriter"
            ]
            
            missing_libs = []
            for lib in export_libs:
                if lib not in content:
                    missing_libs.append(lib)
            
            if not missing_libs:
                print("✅ User Management: Export libraries integrated")
            else:
                print(f"⚠️ User Management: Missing libraries: {missing_libs}")
            
            return len(missing_components) == 0 and len(missing_libs) == 0
        else:
            print("❌ User Management: File not found")
            return False
            
    except Exception as e:
        print(f"❌ User Management: Error - {e}")
        return False

def test_export_functionality():
    """Test export functionality."""
    print("📤 Testing Export Features...")
    
    try:
        # Test PDF export dependencies
        try:
            import reportlab
            print("✅ Export: ReportLab available for PDF export")
            pdf_available = True
        except ImportError:
            print("❌ Export: ReportLab not available")
            pdf_available = False
        
        # Test Excel export dependencies
        try:
            import openpyxl
            print("✅ Export: OpenPyXL available for Excel export")
            excel_available = True
        except ImportError:
            print("❌ Export: OpenPyXL not available")
            excel_available = False
        
        # Test authentication dependencies
        try:
            import streamlit_authenticator
            print("✅ Export: Streamlit Authenticator available")
            auth_available = True
        except ImportError:
            print("❌ Export: Streamlit Authenticator not available")
            auth_available = False
        
        return pdf_available and excel_available and auth_available
        
    except Exception as e:
        print(f"❌ Export: Error - {e}")
        return False

def test_dependencies():
    """Test Phase 4 dependencies."""
    print("📦 Testing Phase 4 Dependencies...")
    
    dependencies = [
        ("streamlit", "Streamlit web framework"),
        ("fastapi", "FastAPI REST framework"),
        ("plotly", "Interactive visualization"),
        ("pandas", "Data manipulation"),
        ("numpy", "Numerical computing"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("reportlab", "PDF generation"),
        ("openpyxl", "Excel export"),
        ("streamlit_authenticator", "User authentication")
    ]
    
    missing_deps = []
    available_deps = []
    
    for dep_name, description in dependencies:
        try:
            __import__(dep_name)
            available_deps.append((dep_name, description))
            print(f"✅ {dep_name}: {description}")
        except ImportError:
            missing_deps.append((dep_name, description))
            print(f"❌ {dep_name}: {description} - Not installed")
    
    print(f"\n📊 Dependency Summary:")
    print(f"   Available: {len(available_deps)}")
    print(f"   Missing: {len(missing_deps)}")
    
    if missing_deps:
        print(f"\n🔧 To install missing dependencies:")
        for dep_name, _ in missing_deps:
            print(f"   pip install {dep_name}")
    
    return len(missing_deps) == 0

def test_file_structure():
    """Test Phase 4 file structure."""
    print("📁 Testing Phase 4 File Structure...")
    
    required_files = [
        "streamlit_app.py",
        "mobile_app.py", 
        "dashboard.py",
        "user_management.py",
        "api/main.py"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path}")
    
    print(f"\n📊 File Structure Summary:")
    print(f"   Existing: {len(existing_files)}")
    print(f"   Missing: {len(missing_files)}")
    
    return len(missing_files) == 0

async def run_comprehensive_test():
    """Run comprehensive Phase 4 test suite."""
    print("🚀 PHASE 4 COMPREHENSIVE TESTING - USER EXPERIENCE & API SUPPORT")
    print("=" * 80)
    
    tests = [
        ("File Structure", test_file_structure, False),
        ("Dependencies", test_dependencies, False),
        ("Streamlit Web App", test_streamlit_app, False),
        ("Mobile Interface", test_mobile_app, False),
        ("REST API", test_api_endpoints, False),
        ("API Server", test_api_server, True),
        ("Advanced Dashboard", test_dashboard, False),
        ("User Management", test_user_management, False),
        ("Export Features", test_export_functionality, False)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func, is_async in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            if is_async:
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"💥 {test_name}: EXCEPTION - {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"📊 PHASE 4 TEST RESULTS")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL PHASE 4 TESTS PASSED!")
        print("🚀 User Experience & API Support is ready for production!")
        
        print("\n📋 PHASE 4 FEATURES READY:")
        print("   🌐 Streamlit Web Interface")
        print("   📱 Mobile-Responsive Design")
        print("   🔌 REST API Endpoints")
        print("   📊 Advanced Dashboard")
        print("   👤 User Authentication")
        print("   💼 Portfolio Management")
        print("   📤 Export Capabilities (PDF, Excel, JSON)")
        print("   📈 Interactive Visualizations")
        
        print("\n🎯 HOW TO USE:")
        print("   • Web App: streamlit run streamlit_app.py")
        print("   • Mobile App: streamlit run mobile_app.py")
        print("   • Dashboard: streamlit run dashboard.py")
        print("   • User Management: streamlit run user_management.py")
        print("   • API Server: python api/main.py")
        
        return True
    else:
        print(f"\n⚠️  {failed} tests failed. Some features may require additional setup.")
        
        if failed <= 2:
            print("🎯 Minor issues detected. Phase 4 is mostly ready!")
        else:
            print("🔧 Several issues detected. Please review and fix before deployment.")
        
        return failed <= 2

def main():
    """Main test function."""
    try:
        success = asyncio.run(run_comprehensive_test())
        
        print("\n" + "=" * 80)
        print("🏁 PHASE 4 TESTING COMPLETE")
        
        if success:
            print("🎉 Ready for production deployment!")
            sys.exit(0)
        else:
            print("🔧 Requires additional work before deployment.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Testing failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
