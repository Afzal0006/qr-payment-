from io import BytesIO
from decimal import Decimal, InvalidOperation
import qrcode
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from pymongo import MongoClient
import os

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8311824260:AAEXchUpld4AlE9Ifa1IPVOcj5sCG1KKLUo")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://afzal99550:afzal99550@cluster0.aqmbh9q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
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
        "Hi! I'm an automatic QR generator bot 🤖\n\n"
        "Commands:\n"
        "/save {unique_command} {upi_id} - Save your UPI command.\n\n"
        "Example:\n/save aQr afzalparwez9955@ybl\n\n"
        "Then use it like: /aQr 50"
    )

# --- /save ---
async def save_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage: /save {unique_command} {upi_id}\nExample: /save aQr afzalparwez9955@ybl"
        )
        return

    unique_command = context.args[0].lower()
    upi_id = context.args[1]

    if collection.find_one({"command": unique_command}):
        await update.message.reply_text("This command is already taken. Please choose another one.")
        return

    collection.insert_one({"command": unique_command, "upi_id": upi_id})
    await update.message.reply_text(
        f"Command /{unique_command} saved successfully! You can now use /{unique_command} <amount> to generate QR."
    )

# --- Dynamic QR handler ---
async def dynamic_qr_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text.split()[0][1:].lower()  # remove "/" 
    data = collection.find_one({"command": cmd})
    if not data:
        await update.message.reply_text("Command not found. Use /save to create your command first.")
        return

    if not context.args:
        await update.message.reply_text(f"Usage: /{cmd} <amount>\nExample: /{cmd} 50")
        return

    try:
        amt = Decimal(context.args[0])
        if amt <= 0 or amt > Decimal("1000000"):
            await update.message.reply_text("Invalid amount. Must be >0 and <= 1,000,000.")
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

    app.run_polling()

if __name__ == "__main__":
    main()
