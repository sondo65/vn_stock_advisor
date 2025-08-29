"""
Optimized Scanner UI Components for Streamlit

UI components for the optimized stock scanner system.
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
from typing import List, Dict, Any

def render_optimized_stock_scanner():
    """Render optimized stock scanner interface."""
    st.markdown("### ⚡ Quét Cổ Phiếu Tối Ưu")
    st.markdown("🎯 **Hệ thống quét thông minh** - Tiết kiệm 60-80% token, tập trung vào cổ phiếu tiềm năng cao")
    
    # Import scanner components
    try:
        from src.vn_stock_advisor.scanner import (
            LightweightStockScanner,
            find_opportunities,
            get_analysis_priorities
        )
        from src.vn_stock_advisor.scanner.priority_ranking import PriorityLevel
        SCANNER_AVAILABLE = True
    except ImportError as e:
        st.error(f"❌ Scanner modules not available: {e}")
        SCANNER_AVAILABLE = False
        return
    
    # Create tabs for different scanner modes
    scanner_tab1, scanner_tab2, scanner_tab3 = st.tabs([
        "🔍 Quét Nhanh", 
        "🎯 Lọc Cơ Hội", 
        "📊 Xếp Hạng Ưu Tiên"
    ])
    
    with scanner_tab1:
        render_lightweight_scanner()
    
    with scanner_tab2:
        render_screening_engine()
    
    with scanner_tab3:
        render_priority_ranking()

def render_lightweight_scanner():
    """Render lightweight scanner interface."""
    st.markdown("#### ⚡ Quét Nhanh Cổ Phiếu")
    st.info("🚀 **Tính năng mới**: Quét nhanh chỉ với phân tích kỹ thuật cơ bản và định giá, tiết kiệm đến 80% token!")
    
    # Configuration
    col1, col2, col3 = st.columns(3)
    
    with col1:
        scan_mode = st.selectbox(
            "🎯 Chế độ quét",
            ["Thị trường phổ biến", "VN30", "HNX30", "Danh sách tùy chỉnh"],
            key="lightweight_scan_mode"
        )
    
    with col2:
        min_score = st.slider(
            "⭐ Điểm tối thiểu",
            0.0, 10.0, 6.0, 0.5,
            help="Điểm càng cao = tiềm năng càng lớn",
            key="lightweight_min_score"
        )
    
    with col3:
        max_results = st.selectbox(
            "📊 Số kết quả tối đa",
            [10, 15, 20, 30],
            index=1,
            key="lightweight_max_results"
        )
    
    # Custom list input
    if scan_mode == "Danh sách tùy chỉnh":
        custom_stocks = st.text_area(
            "📝 Nhập mã cổ phiếu",
            placeholder="VIC, VCB, FPT, HPG, VNM",
            help="Cách nhau bằng dấu phẩy",
            key="lightweight_custom_stocks"
        )
    
    # Advanced options
    with st.expander("⚙️ Tùy chọn nâng cao"):
        col1, col2 = st.columns(2)
        with col1:
            only_buy_watch = st.checkbox(
                "Chỉ hiển thị BUY và WATCH",
                value=True,
                key="lightweight_only_buy_watch"
            )
        with col2:
            use_cache = st.checkbox(
                "Sử dụng cache (tiết kiệm token)",
                value=True,
                key="lightweight_use_cache"
            )
    
    # Scan button
    if st.button("⚡ Quét Nhanh", type="primary", use_container_width=True, key="lightweight_scan"):
        try:
            from src.vn_stock_advisor.scanner.lightweight_scanner import LightweightStockScanner
            
            # Prepare stock list
            if scan_mode == "Thị trường phổ biến":
                scanner = LightweightStockScanner(max_workers=3, use_cache=use_cache)
                stock_list = scanner.get_popular_stocks()[:25]
            elif scan_mode == "VN30":
                stock_list = [
                    'VIC', 'VHM', 'VRE', 'VCB', 'BID', 'CTG', 'TCB', 'MBB', 'ACB', 'TPB',
                    'HPG', 'HSG', 'NKG', 'GVR', 'PLX', 'POW', 'GAS', 'VNM', 'MSN', 'MWG',
                    'FPT', 'VJC', 'HVN', 'SAB', 'BVH', 'CTD', 'PDR', 'KDH', 'DXG', 'STB'
                ]
            elif scan_mode == "HNX30":
                stock_list = [
                    'SHB', 'PVS', 'CEO', 'TNG', 'VCS', 'IDC', 'NVB', 'PVB', 'THD', 'DTD',
                    'MBS', 'BVS', 'PVC', 'VIG', 'NDN', 'VC3', 'PVI', 'TIG', 'VND', 'HUT'
                ]
            else:  # Custom
                if not custom_stocks:
                    st.error("❌ Vui lòng nhập danh sách mã cổ phiếu")
                    return
                stock_list = [s.strip().upper() for s in custom_stocks.split(',') if s.strip()]
            
            # Initialize scanner
            scanner = LightweightStockScanner(max_workers=3, use_cache=use_cache)
            
            # Show progress
            progress_container = st.container()
            with progress_container:
                st.info(f"🔍 Đang quét {len(stock_list)} cổ phiếu...")
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            # Run scan
            start_time = time.time()
            
            with st.spinner("⚡ Đang phân tích nhanh..."):
                status_text.text("🔍 Thu thập dữ liệu cơ bản...")
                progress_bar.progress(30)
                
                results = scanner.scan_stocks_lightweight(
                    stock_list=stock_list,
                    min_score=min_score,
                    only_buy_watch=only_buy_watch,
                    max_results=max_results
                )
                
                progress_bar.progress(100)
            
            scan_time = time.time() - start_time
            
            # Clear progress
            progress_container.empty()
            
            # Display results
            if results:
                st.success(f"✅ Hoàn thành trong {scan_time:.1f}s! Tìm thấy {len(results)} cơ hội")
                display_lightweight_results(results)
                
                # Store results for other tabs
                st.session_state.lightweight_scan_results = results
            else:
                st.warning("⚠️ Không tìm thấy cổ phiếu nào đáp ứng tiêu chí")
                st.info("💡 Thử giảm điểm tối thiểu hoặc bỏ chọn 'Chỉ BUY và WATCH'")
                
        except Exception as e:
            st.error(f"❌ Lỗi: {str(e)}")
            if "rate limit" in str(e).lower():
                st.info("⏱️ Đã gặp giới hạn API. Vui lòng thử lại sau 1-2 phút.")
            else:
                st.info("💡 Có thể do lỗi kết nối hoặc dữ liệu không khả dụng.")

def render_screening_engine():
    """Render screening engine interface."""
    st.markdown("#### 🎯 Lọc Cơ Hội Đầu Tư")
    st.markdown("Áp dụng các bộ lọc thông minh để tìm cơ hội đầu tư cụ thể")
    
    # Check if we have scan results
    if 'lightweight_scan_results' not in st.session_state:
        st.info("💡 Vui lòng chạy 'Quét Nhanh' trước để có dữ liệu lọc")
        
        # Quick scan button
        if st.button("🔍 Quét dữ liệu nhanh", key="quick_scan_for_screening"):
            with st.spinner("Đang quét dữ liệu..."):
                try:
                    from src.vn_stock_advisor.scanner.lightweight_scanner import LightweightStockScanner
                    scanner = LightweightStockScanner(max_workers=3)
                    stock_list = scanner.get_popular_stocks()[:20]
                    results = scanner.scan_stocks_lightweight(stock_list, min_score=4.0, only_buy_watch=False)
                    st.session_state.lightweight_scan_results = results
                    st.success(f"✅ Đã quét {len(results)} cổ phiếu")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi quét dữ liệu: {e}")
        return
    
    results = st.session_state.lightweight_scan_results
    
    if not results:
        st.warning("⚠️ Không có dữ liệu để lọc")
        return
    
    # Filter selection
    col1, col2 = st.columns(2)
    
    with col1:
        filter_descriptions = {
            "value_opportunities": "💎 Cổ phiếu giá trị (P/B thấp, ROE cao)",
            "momentum_plays": "🚀 Xu hướng mạnh (MACD+, MA tăng)",
            "oversold_bounce": "📈 Cơ hội phục hồi (RSI quá bán)",
            "quality_growth": "⭐ Tăng trưởng chất lượng (ROE cao, ổn định)",
            "breakout_candidates": "💥 Ứng viên breakout (Volume tăng, momentum)"
        }
        
        selected_filters = st.multiselect(
            "🎯 Chọn bộ lọc",
            list(filter_descriptions.keys()),
            default=["value_opportunities", "momentum_plays"],
            format_func=lambda x: filter_descriptions[x],
            key="screening_filters"
        )
    
    with col2:
        top_n = st.selectbox(
            "📊 Top picks mỗi loại",
            [3, 5, 8, 10],
            index=1,
            key="screening_top_n"
        )
    
    if st.button("🎯 Áp dụng bộ lọc", key="apply_screening"):
        with st.spinner("Đang lọc cơ hội..."):
            try:
                from src.vn_stock_advisor.scanner import find_opportunities
                opportunities = find_opportunities(results)
                
                # Display opportunities by category
                for filter_name in selected_filters:
                    if filter_name in opportunities and opportunities[filter_name]:
                        stocks = opportunities[filter_name]
                        
                        st.markdown(f"##### {filter_descriptions[filter_name]}")
                        
                        # Create mini table for each category
                        category_data = []
                        for stock in stocks[:top_n]:
                            category_data.append({
                                'Symbol': stock['symbol'],
                                'Score': f"{stock.get('filter_score', 0):.1f}",
                                'P/B': f"{stock.get('pb_ratio', 0):.2f}",
                                'RSI': f"{stock.get('rsi', 0):.1f}",
                                'Trend': stock.get('ma_trend', 'N/A'),
                                'MACD': stock.get('macd_signal', 'N/A')
                            })
                        
                        if category_data:
                            df = pd.DataFrame(category_data)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Overall top picks
                if "overall_top" in opportunities and opportunities["overall_top"]:
                    st.markdown("##### 🏆 Top Picks Tổng Thể")
                    display_opportunity_summary(opportunities["overall_top"][:top_n])
                    
            except Exception as e:
                st.error(f"❌ Lỗi lọc cơ hội: {e}")

def render_priority_ranking():
    """Render priority ranking interface."""
    st.markdown("#### 📊 Xếp Hạng Ưu Tiên Phân Tích")
    st.markdown("Xếp hạng cổ phiếu theo độ ưu tiên để tối ưu hóa thời gian phân tích chuyên sâu")
    
    # Check if we have scan results
    if 'lightweight_scan_results' not in st.session_state:
        st.info("💡 Vui lòng chạy 'Quét Nhanh' trước để có dữ liệu xếp hạng")
        return
    
    results = st.session_state.lightweight_scan_results
    
    if not results:
        st.warning("⚠️ Không có dữ liệu để xếp hạng")
        return
    
    # Configuration
    col1, col2 = st.columns(2)
    
    with col1:
        show_all_priorities = st.checkbox(
            "Hiển thị tất cả mức ưu tiên",
            value=False,
            key="show_all_priorities"
        )
    
    with col2:
        max_per_priority = st.selectbox(
            "Số lượng tối đa mỗi mức",
            [3, 5, 8, 10],
            index=1,
            key="max_per_priority"
        )
    
    if st.button("📊 Xếp hạng ưu tiên", key="create_rankings"):
        with st.spinner("Đang xếp hạng..."):
            try:
                from src.vn_stock_advisor.scanner import get_analysis_priorities
                from src.vn_stock_advisor.scanner.priority_ranking import PriorityLevel
                
                # Get priority rankings
                priority_queue = get_analysis_priorities(results)
                
                # Display by priority level
                priority_colors = {
                    PriorityLevel.CRITICAL: "🔴",
                    PriorityLevel.HIGH: "🟠", 
                    PriorityLevel.MEDIUM: "🟡",
                    PriorityLevel.LOW: "🟢",
                    PriorityLevel.SKIP: "⚪"
                }
                
                priority_descriptions = {
                    PriorityLevel.CRITICAL: "Phân tích ngay lập tức",
                    PriorityLevel.HIGH: "Phân tích trong 1 giờ",
                    PriorityLevel.MEDIUM: "Phân tích trong ngày",
                    PriorityLevel.LOW: "Phân tích khi rảnh",
                    PriorityLevel.SKIP: "Bỏ qua"
                }
                
                total_high_priority = 0
                
                for priority_level in [PriorityLevel.CRITICAL, PriorityLevel.HIGH, PriorityLevel.MEDIUM, PriorityLevel.LOW]:
                    stocks = priority_queue.get(priority_level, [])
                    
                    if stocks and (show_all_priorities or priority_level.value <= 3):
                        emoji = priority_colors[priority_level]
                        desc = priority_descriptions[priority_level]
                        
                        st.markdown(f"##### {emoji} {priority_level.name} - {desc}")
                        
                        if priority_level.value <= 2:  # CRITICAL or HIGH
                            total_high_priority += len(stocks)
                        
                        # Display stocks in this priority
                        priority_data = []
                        for stock in stocks[:max_per_priority]:
                            priority_data.append({
                                'Symbol': stock.symbol,
                                'Score': f"{stock.overall_score:.1f}",
                                'Analysis': stock.recommended_analysis_type,
                                'Time': f"{stock.estimated_analysis_time}min",
                                'Confidence': f"{stock.confidence_level:.0%}",
                                'Notes': stock.notes[0] if stock.notes else ""
                            })
                        
                        if priority_data:
                            df = pd.DataFrame(priority_data)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        # Quick action buttons for high priority
                        if priority_level.value <= 2 and priority_data:
                            st.markdown("**🚀 Hành động nhanh:**")
                            cols = st.columns(min(len(priority_data), 4))
                            for i, (col, stock_data) in enumerate(zip(cols, priority_data)):
                                with col:
                                    if st.button(
                                        f"Phân tích {stock_data['Symbol']}", 
                                        key=f"quick_analyze_{stock_data['Symbol']}_{priority_level.name}"
                                    ):
                                        st.info(f"🔄 Chuyển đến phân tích chuyên sâu cho {stock_data['Symbol']}")
                                        # Set session state to trigger analysis
                                        st.session_state.selected_stock = stock_data['Symbol']
                                        st.experimental_rerun()
                
                # Summary
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("🔥 Ưu tiên cao", total_high_priority)
                
                with col2:
                    total_analysis_time = sum(
                        stock.estimated_analysis_time 
                        for stocks in priority_queue.values() 
                        for stock in stocks
                        if stock.priority_level != PriorityLevel.SKIP
                    )
                    st.metric("⏱️ Tổng thời gian", f"{total_analysis_time}min")
                
                with col3:
                    efficiency_score = (total_high_priority / len(results) * 100) if results else 0
                    st.metric("⚡ Hiệu quả", f"{efficiency_score:.0f}%")
            
            except Exception as e:
                st.error(f"❌ Lỗi xếp hạng: {e}")

def display_lightweight_results(results):
    """Display lightweight scanner results."""
    if not results:
        return
    
    st.markdown("#### 📊 Kết Quả Quét Nhanh")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    buy_count = len([r for r in results if r.recommendation == "BUY"])
    watch_count = len([r for r in results if r.recommendation == "WATCH"])
    avg_score = sum(r.overall_score for r in results) / len(results)
    avg_pb = sum(r.pb_ratio for r in results if r.pb_ratio > 0) / len([r for r in results if r.pb_ratio > 0]) if any(r.pb_ratio > 0 for r in results) else 0
    
    with col1:
        st.metric("🟢 BUY signals", buy_count)
    with col2:
        st.metric("🟡 WATCH signals", watch_count)
    with col3:
        st.metric("⭐ Điểm TB", f"{avg_score:.1f}")
    with col4:
        st.metric("📊 P/B TB", f"{avg_pb:.2f}")
    
    # Results table
    df_data = []
    for i, result in enumerate(results, 1):
        df_data.append({
            'Rank': i,
            'Symbol': result.symbol,
            'Rec': result.recommendation,
            'Score': f"{result.overall_score:.1f}",
            'Value': f"{result.value_score:.1f}",
            'Momentum': f"{result.momentum_score:.1f}",
            'P/B': f"{result.pb_ratio:.2f}",
            'RSI': f"{result.rsi:.1f}",
            'MACD': result.macd_signal,
            'Trend': result.ma_trend,
            'Conf': f"{result.confidence:.0%}"
        })
    
    df = pd.DataFrame(df_data)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("🏆", width="tiny"),
            "Symbol": st.column_config.TextColumn("📊", width="small"),
            "Rec": st.column_config.TextColumn("💡", width="tiny"),
            "Score": st.column_config.TextColumn("⭐", width="tiny"),
            "Value": st.column_config.TextColumn("💎", width="tiny"),
            "Momentum": st.column_config.TextColumn("🚀", width="tiny"),
            "P/B": st.column_config.TextColumn("📈", width="tiny"),
            "RSI": st.column_config.TextColumn("📊", width="tiny"),
            "MACD": st.column_config.TextColumn("📈", width="tiny"),
            "Trend": st.column_config.TextColumn("↗️", width="tiny"),
            "Conf": st.column_config.TextColumn("🎯", width="tiny")
        }
    )
    
    # Action buttons for top picks
    if buy_count > 0:
        st.markdown("#### 🚀 Hành Động Nhanh")
        buy_stocks = [r for r in results if r.recommendation == "BUY"]
        
        cols = st.columns(min(len(buy_stocks), 5))
        for i, (col, stock) in enumerate(zip(cols, buy_stocks[:5])):
            with col:
                if st.button(
                    f"📈 Phân tích {stock.symbol}", 
                    key=f"analyze_from_scanner_{stock.symbol}"
                ):
                    # Set for analysis in main tab
                    st.session_state.selected_stock = stock.symbol
                    st.info(f"🔄 Đã chọn {stock.symbol} để phân tích chuyên sâu")

def display_opportunity_summary(opportunities):
    """Display opportunity summary."""
    if not opportunities:
        return
    
    summary_data = []
    for i, stock in enumerate(opportunities, 1):
        summary_data.append({
            'Rank': i,
            'Symbol': stock['symbol'],
            'Score': f"{stock.get('filter_score', 0):.1f}",
            'P/B': f"{stock.get('pb_ratio', 0):.2f}",
            'P/E': f"{stock.get('pe_ratio', 0):.1f}",
            'RSI': f"{stock.get('rsi', 0):.1f}",
            'MACD': stock.get('macd_signal', 'N/A'),
            'Industry': stock.get('industry', 'N/A')
        })
    
    df = pd.DataFrame(summary_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_scanner_info_panel():
    """Render info panel about scanner benefits."""
    st.markdown("#### 💡 Về Hệ Thống Scanner Tối Ưu")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **⚡ Tính năng chính:**
        - 🔍 Quét nhanh với token usage tối thiểu
        - 🎯 Lọc theo nhiều tiêu chí thông minh
        - 📊 Xếp hạng ưu tiên phân tích
        - 💰 Tiết kiệm 60-80% token với cache
        - 🚀 Workflow tự động hóa
        """)
    
    with col2:
        st.markdown("""
        **📈 Lợi ích:**
        - ⏱️ Nhanh hơn 5-10x so với phân tích đầy đủ
        - 🎯 Tập trung vào cổ phiếu tiềm năng cao
        - 💸 Giảm chi phí API đáng kể
        - 🔄 Kết quả nhất quán và tin cậy
        - 📊 Báo cáo chi tiết và trực quan
        """)
    
    # Performance metrics (if available)
    if hasattr(st.session_state, 'scanner_stats'):
        stats = st.session_state.scanner_stats
        
        st.markdown("#### 📊 Thống Kê Hiệu Suất")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🔍 Đã quét", f"{stats.get('total_scanned', 0)} cổ phiếu")
        with col2:
            st.metric("💰 Token tiết kiệm", f"{stats.get('tokens_saved', 0):,}")
        with col3:
            st.metric("⚡ Cache hit rate", f"{stats.get('cache_hit_rate', 0):.1f}%")
        with col4:
            st.metric("⏱️ Thời gian TB", f"{stats.get('avg_time', 0):.1f}s")
