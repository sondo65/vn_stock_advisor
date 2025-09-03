import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, time, timezone, timedelta
from typing import List, Optional, Tuple
from enum import Enum
from collections import deque

import aiosqlite
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    Defaults,
)


load_dotenv()


_env_db = os.getenv("TELEGRAM_PORTFOLIO_DB")
DB_PATH = (
    _env_db if (_env_db is not None and _env_db.strip() != "") else os.path.join(os.path.dirname(__file__), "portfolio.sqlite3")
)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEFAULT_CHAT_ID = os.getenv("DEFAULT_CHAT_ID")


class MarketData:
    @staticmethod
    async def get_price(symbol: str) -> Optional[float]:
        """Fetch latest price for a symbol. Replace with real-time source as needed.

        Default implementation tries vnstock if available, otherwise returns None.
        """
        # First try vnstock Vnstock class with multiple sources (VCI/TCBS/DNSE/SSI)
        try:
            from vnstock import Vnstock

            today = datetime.now().date()
            start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            for source in ("VCI", "TCBS", "DNSE", "SSI"):
                try:
                    stock = Vnstock().stock(symbol=symbol, source=source)
                    price_df = stock.quote.history(
                        start=start_date,
                        end=end_date,
                        interval="1D",
                    )
                    if price_df is not None and not price_df.empty:
                        # use last non-null close
                        closes = price_df["close"].dropna()
                        if not closes.empty:
                            return float(closes.iloc[-1])
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback to legacy helper stock_historical_data
        try:
            from vnstock import stock_historical_data

            today = datetime.now().date()
            start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            data = stock_historical_data(
                symbol=symbol,
                start=start_date,
                end=end_date,
                resolution="1D",
            )
            if data is None or len(data) == 0:
                return None
            last_close = None
            for idx in range(len(data) - 1, -1, -1):
                try:
                    val = float(data.iloc[idx]["close"])  # type: ignore[index]
                    last_close = val
                    break
                except Exception:
                    continue
            if last_close is None:
                return None
            return last_close
        except Exception:
            return None


class PredictionDecision(str, Enum):
    BUY_MORE = "BUY_MORE"
    HOLD = "HOLD"
    SELL = "SELL"


class PredictionResult(BaseModel):
    symbol: str
    decision: PredictionDecision
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: Optional[str] = None


class PredictionEngine:
    @staticmethod
    async def predict(symbol: str) -> PredictionResult:
        """Plug point: call your existing model/pipeline to decide action.

        Replace this stub with a call into your advisor. For now, we return HOLD
        with medium confidence.
        """
        # TODO: Integrate with your existing advisor decision output
        return PredictionResult(
            symbol=symbol,
            decision=PredictionDecision.HOLD,
            confidence=0.5,
            rationale="Default placeholder decision; integrate your model here.",
        )


CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        chat_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        quantity REAL NOT NULL,
        avg_cost REAL NOT NULL,
        UNIQUE(user_id, symbol),
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL, -- BUY / SELL
        quantity REAL NOT NULL,
        price REAL NOT NULL,
        ts TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS settings (
        user_id INTEGER PRIMARY KEY,
        schedule_hhmm TEXT, -- e.g., 08:15 (24h format, local time)
        timezone_offset_min INTEGER DEFAULT 0
    );
    """,
]


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        for sql in CREATE_TABLES_SQL:
            await db.execute(sql)
        await db.commit()


async def upsert_user(user_id: int, chat_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, chat_id, created_at) VALUES (?, ?, ?)",
            (user_id, chat_id, now),
        )
        await db.commit()


async def get_user_chat_id(user_id: int) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT chat_id FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def add_transaction_and_update_position(
    user_id: int,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
) -> None:
    symbol = symbol.upper().strip()
    ts = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO transactions (user_id, symbol, side, quantity, price, ts) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, symbol, side, quantity, price, ts),
        )

        # Fetch current position
        async with db.execute(
            "SELECT quantity, avg_cost FROM positions WHERE user_id=? AND symbol=?",
            (user_id, symbol),
        ) as cur:
            row = await cur.fetchone()

        if side.upper() == "BUY":
            if row:
                old_qty, old_avg = float(row[0]), float(row[1])
                new_qty = old_qty + quantity
                new_avg = (old_qty * old_avg + quantity * price) / new_qty if new_qty != 0 else 0.0
                await db.execute(
                    "UPDATE positions SET quantity=?, avg_cost=? WHERE user_id=? AND symbol=?",
                    (new_qty, new_avg, user_id, symbol),
                )
            else:
                await db.execute(
                    "INSERT INTO positions (user_id, symbol, quantity, avg_cost) VALUES (?, ?, ?, ?)",
                    (user_id, symbol, quantity, price),
                )
        elif side.upper() == "SELL":
            if row:
                old_qty, old_avg = float(row[0]), float(row[1])
                new_qty = old_qty - quantity
                if new_qty < 0:
                    new_qty = 0.0
                if new_qty == 0:
                    await db.execute(
                        "DELETE FROM positions WHERE user_id=? AND symbol=?",
                        (user_id, symbol),
                    )
                else:
                    # Average cost unchanged on sell
                    await db.execute(
                        "UPDATE positions SET quantity=? WHERE user_id=? AND symbol=?",
                        (new_qty, user_id, symbol),
                    )
            else:
                # Selling without position: record transaction only
                pass
        else:
            raise ValueError("side must be BUY or SELL")

        await db.commit()


async def get_positions(user_id: int) -> List[Tuple[str, float, float]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT symbol, quantity, avg_cost FROM positions WHERE user_id=? ORDER BY symbol",
            (user_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [(str(r[0]), float(r[1]), float(r[2])) for r in rows]


async def get_pnl_report(user_id: int) -> List[Tuple[str, float, float, Optional[float], Optional[float]]]:
    positions = await get_positions(user_id)
    report: List[Tuple[str, float, float, Optional[float], Optional[float]]] = []
    for symbol, qty, avg_cost in positions:
        price = await MarketData.get_price(symbol)
        pnl = None
        if price is not None:
            pnl = (price - avg_cost) * qty
        report.append((symbol, qty, avg_cost, price, pnl))
    return report


async def get_transactions(user_id: int, symbol: str) -> List[Tuple[str, float, float, str]]:
    """Return list of transactions for a symbol ordered by timestamp.

    Each item: (side, quantity, price, ts)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT side, quantity, price, ts FROM transactions WHERE user_id=? AND symbol=? ORDER BY ts ASC",
            (user_id, symbol),
        ) as cur:
            rows = await cur.fetchall()
            return [
                (str(r[0]), float(r[1]), float(r[2]), str(r[3])) for r in rows
            ]


async def compute_fifo_lots(user_id: int, symbol: str) -> List[Tuple[float, float]]:
    """Compute remaining lots using FIFO from transactions.

    Returns list of (quantity, unit_cost) for remaining holdings.
    """
    txs = await get_transactions(user_id, symbol)
    lots: deque[Tuple[float, float]] = deque()
    for side, qty, price, _ in txs:
        if side.upper() == "BUY":
            lots.append((qty, price))
        elif side.upper() == "SELL":
            remaining = qty
            while remaining > 0 and lots:
                lot_qty, lot_price = lots[0]
                if lot_qty > remaining:
                    lots[0] = (lot_qty - remaining, lot_price)
                    remaining = 0
                else:
                    remaining -= lot_qty
                    lots.popleft()
            # If selling more than held, ignore excess
        else:
            continue
    return list(lots)


async def compute_effective_avg_cost_fifo(user_id: int, symbol: str) -> Optional[float]:
    lots = await compute_fifo_lots(user_id, symbol)
    if not lots:
        return None
    total_qty = sum(q for q, _ in lots)
    if total_qty <= 0:
        return None
    total_cost = sum(q * p for q, p in lots)
    return total_cost / total_qty


def parse_hhmm(hhmm: str) -> Optional[time]:
    try:
        parts = hhmm.strip().split(":")
        if len(parts) != 2:
            return None
        hh, mm = int(parts[0]), int(parts[1])
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            return None
        return time(hour=hh, minute=mm)
    except Exception:
        return None


async def set_schedule(user_id: int, hhmm: str) -> bool:
    t = parse_hhmm(hhmm)
    if t is None:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO settings (user_id, schedule_hhmm) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET schedule_hhmm=excluded.schedule_hhmm",
            (user_id, hhmm),
        )
        await db.commit()
    return True


async def get_schedule(user_id: int) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT schedule_hhmm FROM settings WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return str(row[0]) if row and row[0] else None


async def analyze_and_notify(application: Application, user_id: int, chat_id: str) -> None:
    positions = await get_positions(user_id)
    if not positions:
        await application.bot.send_message(chat_id=chat_id, text="Danh mục trống.")
        return

    lines: List[str] = ["Kết quả phân tích danh mục:"]
    for symbol, qty, avg_cost in positions:
        price = await MarketData.get_price(symbol)
        pred = await PredictionEngine.predict(symbol)
        decision = pred.decision
        conf_pct = int(pred.confidence * 100)
        price_str = f"{price:.2f}" if price is not None else "N/A"
        pnl_val = (price - avg_cost) * qty if price is not None else None
        pnl_str = f"{pnl_val:.2f}" if pnl_val is not None else "N/A"
        lines.append(
            f"- {symbol}: {decision} (conf {conf_pct}%), Giá={price_str}, SL={qty:g}, Giá vốn={avg_cost:.2f}, Lãi/lỗ={pnl_str}"
        )
    await application.bot.send_message(chat_id=chat_id, text="\n".join(lines))


async def reset_user_data(application: Application, user_id: int) -> None:
    """Delete user's positions, transactions, and settings. Keep user row for chat mapping.

    Also remove any scheduled jobs for this user.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM positions WHERE user_id=?", (user_id,))
        await db.execute("DELETE FROM transactions WHERE user_id=?", (user_id,))
        await db.execute("DELETE FROM settings WHERE user_id=?", (user_id,))
        await db.commit()
    # Remove scheduled jobs if JobQueue is available
    if application.job_queue is not None:
        job_name = f"daily_analysis_{user_id}"
        for job in application.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()


# Telegram command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    assert update.effective_chat is not None
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    await upsert_user(user_id, chat_id)
    await update.message.reply_text(
        "Xin chào! Bot quản lý danh mục đã sẵn sàng. Dùng /help để xem hướng dẫn."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Lệnh khả dụng:\n"
        "/add <mã> <sl> <giá> — mua thêm\n"
        "/sell <mã> <sl> <giá> — bán\n"
        "/portfolio — xem danh mục\n"
        "/pnl — thống kê lãi lỗ theo giá hiện tại\n"
        "/analyze_now — phân tích ngay và gợi ý hành động\n"
        "/set_schedule <HH:MM> — đặt giờ chạy phân tích hàng ngày (theo giờ máy)\n"
        "/reset — xóa toàn bộ dữ liệu danh mục (cần xác nhận)\n"
        "/confirm_reset — xác nhận xóa dữ liệu\n"
        "/cancel_reset — hủy yêu cầu xóa\n"
    )
    await update.message.reply_text(text)


async def add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    if len(context.args) != 3:
        await update.message.reply_text("Cú pháp: /add <mã> <sl> <giá>")
        return
    symbol = context.args[0].upper()
    try:
        qty = float(context.args[1])
        price = float(context.args[2])
    except ValueError:
        await update.message.reply_text("SL và giá phải là số.")
        return
    await add_transaction_and_update_position(user_id, symbol, "BUY", qty, price)
    await update.message.reply_text(f"Đã mua {qty:g} {symbol} giá {price:.2f}.")


async def sell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    if len(context.args) != 3:
        await update.message.reply_text("Cú pháp: /sell <mã> <sl> <giá>")
        return
    symbol = context.args[0].upper()
    try:
        qty = float(context.args[1])
        price = float(context.args[2])
    except ValueError:
        await update.message.reply_text("SL và giá phải là số.")
        return
    await add_transaction_and_update_position(user_id, symbol, "SELL", qty, price)
    await update.message.reply_text(f"Đã bán {qty:g} {symbol} giá {price:.2f}.")


async def portfolio_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    positions = await get_positions(user_id)
    if not positions:
        await update.message.reply_text("Danh mục trống.")
        return
    # Build a simple monospaced table
    rows = []
    header = ("Mã", "Số lượng", "Giá vốn", "Giá hiện tại", "Lãi/lỗ", "Stoploss")
    rows.append(header)
    for symbol, qty, avg_cost in positions:
        # Recompute avg_cost using FIFO for accuracy after sells
        fifo_avg = await compute_effective_avg_cost_fifo(user_id, symbol)
        effective_avg = fifo_avg if fifo_avg is not None else avg_cost
        price = await MarketData.get_price(symbol)
        price_str = f"{price:.2f}" if price is not None else "N/A"
        pnl_val = ((price - effective_avg) * qty) if price is not None else None
        pnl_str = f"{pnl_val:.2f}" if pnl_val is not None else "N/A"
        stoploss_val = effective_avg * 0.92  # default 8% stoploss below cost
        stoploss_str = f"{stoploss_val:.2f}"
        rows.append((symbol, f"{qty:g}", f"{effective_avg:.2f}", price_str, pnl_str, stoploss_str))

    # Column widths
    col_widths = [0, 0, 0, 0, 0, 0]
    for r in rows:
        for i, val in enumerate(r):
            col_widths[i] = max(col_widths[i], len(str(val)))

    def fmt_row(r: tuple) -> str:
        return (
            f"{str(r[0]).ljust(col_widths[0])}  "
            f"{str(r[1]).rjust(col_widths[1])}  "
            f"{str(r[2]).rjust(col_widths[2])}  "
            f"{str(r[3]).rjust(col_widths[3])}  "
            f"{str(r[4]).rjust(col_widths[4])}  "
            f"{str(r[5]).rjust(col_widths[5])}"
        )

    table_lines = [
        fmt_row(rows[0]),
        fmt_row((
            "-" * col_widths[0],
            "-" * col_widths[1],
            "-" * col_widths[2],
            "-" * col_widths[3],
            "-" * col_widths[4],
            "-" * col_widths[5],
        )),
    ]
    for r in rows[1:]:
        table_lines.append(fmt_row(r))

    msg_lines = ["Danh mục hiện tại:", *table_lines]
    await update.message.reply_text("\n".join(msg_lines))


async def pnl_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    report = await get_pnl_report(user_id)
    if not report:
        await update.message.reply_text("Danh mục trống.")
        return
    lines = ["PnL theo giá hiện tại:"]
    total_pnl = 0.0
    for symbol, qty, avg_cost, price, pnl in report:
        price_str = f"{price:.2f}" if price is not None else "N/A"
        pnl_str = f"{pnl:.2f}" if pnl is not None else "N/A"
        if pnl is not None:
            total_pnl += pnl
        lines.append(
            f"- {symbol}: Giá={price_str}, SL={qty:g}, Giá vốn={avg_cost:.2f}, Lãi/lỗ={pnl_str}"
        )
    lines.append(f"Tổng lãi/lỗ: {total_pnl:.2f}")
    await update.message.reply_text("\n".join(lines))


async def analyze_now_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    assert update.effective_chat is not None
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    await analyze_and_notify(context.application, user_id, chat_id)


async def set_schedule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    if len(context.args) != 1:
        await update.message.reply_text("Cú pháp: /set_schedule <HH:MM>")
        return
    ok = await set_schedule(user_id, context.args[0])
    if not ok:
        await update.message.reply_text("Giờ không hợp lệ. Ví dụ: 08:30")
        return
    await update.message.reply_text("Đã lưu giờ chạy hàng ngày.")
    # Reschedule jobs for this user
    await schedule_user_job(context.application, user_id)


# Pending reset state (in-memory with TTL)
PENDING_RESET: dict[int, datetime] = {}
RESET_TTL_SECONDS = 120


async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    PENDING_RESET[user_id] = datetime.now(timezone.utc)
    await update.message.reply_text(
        "Bạn có chắc muốn xóa toàn bộ danh mục và lịch?\n"
        "Gõ /confirm_reset trong vòng 2 phút để xác nhận, hoặc /cancel_reset để hủy."
    )


async def confirm_reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    assert update.effective_chat is not None
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    ts = PENDING_RESET.get(user_id)
    if ts is None:
        await update.message.reply_text("Không có yêu cầu xóa nào đang chờ.")
        return
    if (datetime.now(timezone.utc) - ts).total_seconds() > RESET_TTL_SECONDS:
        del PENDING_RESET[user_id]
        await update.message.reply_text("Yêu cầu xóa đã hết hạn. Hãy gõ /reset lại nếu vẫn muốn xóa.")
        return
    # Proceed reset
    await reset_user_data(context.application, user_id)
    del PENDING_RESET[user_id]
    await context.application.bot.send_message(chat_id=chat_id, text="Đã xóa toàn bộ danh mục, giao dịch và lịch.")


async def cancel_reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    if user_id in PENDING_RESET:
        del PENDING_RESET[user_id]
        await update.message.reply_text("Đã hủy yêu cầu xóa dữ liệu.")
    else:
        await update.message.reply_text("Không có yêu cầu xóa nào đang chờ.")


async def schedule_user_job(app: Application, user_id: int) -> None:
    hhmm = await get_schedule(user_id)
    chat_id = await get_user_chat_id(user_id)
    if not hhmm or not chat_id:
        return
    t = parse_hhmm(hhmm)
    if t is None:
        return
    job_name = f"daily_analysis_{user_id}"
    # Remove old job if exists
    for job in app.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()
    # Schedule new daily job (local time of the machine)
    app.job_queue.run_daily(
        callback=lambda ctx: asyncio.create_task(
            analyze_and_notify(app, user_id, chat_id)
        ),
        time=t,
        name=job_name,
    )


async def bootstrap_schedules(app: Application) -> None:
    # Load all users with schedules and register their jobs
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM settings WHERE schedule_hhmm IS NOT NULL") as cur:
            rows = await cur.fetchall()
            for (user_id,) in rows:
                await schedule_user_job(app, int(user_id))


async def push_to_default_chat_if_set(app: Application, text: str) -> None:
    if DEFAULT_CHAT_ID:
        try:
            await app.bot.send_message(chat_id=DEFAULT_CHAT_ID, text=text)
        except Exception:
            pass


async def _post_init(application: Application) -> None:
    await init_db()
    await bootstrap_schedules(application)
    await push_to_default_chat_if_set(application, "Bot đã khởi động trên máy local.")


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in environment.")

    application: Application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .defaults(Defaults())
        .post_init(_post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("add", add_cmd))
    application.add_handler(CommandHandler("sell", sell_cmd))
    application.add_handler(CommandHandler("portfolio", portfolio_cmd))
    application.add_handler(CommandHandler("pnl", pnl_cmd))
    application.add_handler(CommandHandler("analyze_now", analyze_now_cmd))
    application.add_handler(CommandHandler("set_schedule", set_schedule_cmd))
    application.add_handler(CommandHandler("reset", reset_cmd))
    application.add_handler(CommandHandler("confirm_reset", confirm_reset_cmd))
    application.add_handler(CommandHandler("cancel_reset", cancel_reset_cmd))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()


