from io import BytesIO
from decimal import Decimal, InvalidOperation

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import qrcode

# ==== CONFIG ====
BOT_TOKEN = "8311824260:AAEXchUpld4AlE9Ifa1IPVOcj5sCG1KKLUo"  # <- AAPKA TOKEN
UPI_ID = "afzalparwez9955@ybl"   # <- AAPKA UPI
PAYEE_NAME = "Afzal Parwez"      # <- Naam jo dikhana hai
CURRENCY = "INR"
# ================

def build_upi_link(amount: Decimal) -> str:
    am_str = f"{amount:.2f}"  # 2 decimal tak
    return f"upi://pay?pa={UPI_ID}&pn={PAYEE_NAME}&am={am_str}&cu={CURRENCY}"

def make_qr_png_bytes(data: str) -> BytesIO:
    img = qrcode.make(data)
    bio = BytesIO()
    bio.name = "qr.png"
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio

async def qr_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /qr <amount>\nExample: /qr 67")
        return

    try:
        amt = Decimal(context.args[0])
        if amt <= 0:
            raise InvalidOperation
        if amt > Decimal("1000000"):
            await update.message.reply_text("Amount bahut bada hai.")
            return
    except InvalidOperation:
        await update.message.reply_text("Invalid amount. Example: /qr 67  ya  /qr 88.50")
        return

    upi_link = build_upi_link(amt)
    qr_bytes = make_qr_png_bytes(upi_link)

    caption = (
        f"UPI: `{UPI_ID}`\n"
        f"Name: {PAYEE_NAME}\n"
        f"Amount: ₹{amt:.2f}\n\n"
        f"Scan karke pay karein."
    )

    await update.message.reply_photo(
        photo=qr_bytes,
        caption=caption,
        parse_mode="Markdown"
    )

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! /qr <amount> bhejiye.\nExample: /qr 67"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("qr", qr_cmd))

    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
