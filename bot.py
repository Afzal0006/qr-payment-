from io import BytesIO
from decimal import Decimal, InvalidOperation
import qrcode
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from pymongo import MongoClient
import re

# ================= CONFIG =================
BOT_TOKEN = "8178528811:AAFU-apXWWMK-rNFl2EyiHdOhAnbjLkqJBQ"
MONGO_URI = "mongodb+srv://afzal99550:afzal99550@cluster0.aqmbh9q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "qr_bot"
COLLECTION_NAME = "commands"
CURRENCY = "INR"
# ==========================================

# MongoDB client
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# --- QR generator ---
def build_upi_link(amount: Decimal, upi_id: str) -> str:
    am_str = f"{amount:.2f}"
    return f"upi://pay?pa={upi_id}&am={am_str}&cu={CURRENCY}"

def make_qr_png_bytes(data: str) -> BytesIO:
    img = qrcode.make(data)
    bio = BytesIO()
    bio.name = "qr.png"
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio

# --- /start ---
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I'm a QR generator bot 🤖\n\n"
        "Commands:\n"
        "/save {unique_command} {upi_id} - Save your UPI command.\n"
        "Example: /save aQr afzalparwez9955@ybl\n"
        "Then use: /aQr 50"
    )

# --- /save ---
async def save_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage: /save {unique_command} {upi_id}\nExample: /save aQr afzalparwez9955@ybl"
        )
        return

    unique_command = context.args[0].strip().lower()
    upi_id = context.args[1].strip()

    if not re.fullmatch(r'[a-zA-Z0-9]+', unique_command):
        await update.message.reply_text("Command should be alphanumeric only (no spaces/special chars).")
        return

    if collection.find_one({"command": unique_command}):
        await update.message.reply_text("This command is already taken. Please choose another one.")
        return

    collection.insert_one({"command": unique_command, "upi_id": upi_id})
    await update.message.reply_text(
        f"Command /{unique_command} saved successfully! Use /{unique_command} <amount> to generate QR."
    )

# --- Dynamic QR handler ---
async def dynamic_qr_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.startswith("/"):
        return

    parts = update.message.text.split()
    cmd = parts[0][1:].strip().lower()
    args = parts[1:]

    data = collection.find_one({"command": cmd})
    if not data:
        return

    if len(args) != 1:
        await update.message.reply_text(f"Usage: /{cmd} <amount>\nExample: /{cmd} 50")
        return

    try:
        amt = Decimal(args[0])
        if amt <= 0 or amt > Decimal("1000000"):
            await update.message.reply_text("Invalid amount. Must be >0 and <=1,000,000.")
            return
    except InvalidOperation:
        await update.message.reply_text(f"Invalid amount. Example: /{cmd} 50 or /{cmd} 88.50")
        return

    upi_id = data["upi_id"]
    upi_link = build_upi_link(amt, upi_id)
    qr_bytes = make_qr_png_bytes(upi_link)

    caption = f"UPI: `{upi_id}`\nAmount: ₹{amt:.2f}\nScan to pay."
    await update.message.reply_photo(photo=qr_bytes, caption=caption, parse_mode="Markdown")

# --- Main ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("save", save_cmd))
    app.add_handler(MessageHandler(filters.COMMAND, dynamic_qr_cmd))

    # Heroku ke liye stable run_polling
    app.run_polling()

if __name__ == "__main__":
    main()
