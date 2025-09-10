import asyncio
from telegram_portfolio_bot import IntrinsicValueCalculator


async def main() -> None:
    symbol = "VIC"
    print(f"=== Intrinsic Value Test for {symbol} ===")

    # Lấy dữ liệu tài chính thực từ vnstock (có tích hợp PECalculator)
    fin = await IntrinsicValueCalculator.get_financial_data(symbol)
    if not fin:
        print("❌ Cannot fetch financial data")
        return

    print("Financial data:")
    for k in [
        "current_price",
        "eps",
        "book_value_per_share",
        "roe",
        "shares_outstanding",
        "source_pe",
    ]:
        print(f"  {k}: {fin.get(k)}")

    # Tính P/E intrinsic với điều chỉnh đã thêm
    pe = IntrinsicValueCalculator.calculate_pe_intrinsic_value(fin)
    print("\nP/E intrinsic:")
    print(pe)

    # Tính Graham (có thể None nếu thiếu BVPS/EPS hợp lệ)
    graham = IntrinsicValueCalculator.calculate_graham_intrinsic_value(fin)
    print("\nGraham intrinsic:")
    print(graham)

    # Tính P/B (fallback theo BVPS; có thể None nếu BVPS 0)
    pb = IntrinsicValueCalculator.calculate_pb_intrinsic_value(fin)
    print("\nP/B intrinsic:")
    print(pb)

    # Weighted khi có đủ
    weighted = IntrinsicValueCalculator.calculate_weighted_intrinsic_value(
        dcf_result=None, pe_result=pe, graham_result=graham, pb_result=pb
    )
    print("\nWeighted intrinsic:")
    print(weighted)


if __name__ == "__main__":
    asyncio.run(main())


