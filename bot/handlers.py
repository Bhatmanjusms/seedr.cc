import os
from seedrcc import Login, Seedr
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)

TOKEN_FILE = "seedr_token.txt"

class SeedrBot:
    def __init__(self):
        self.pending_auth = {}  # user_id: (Login instance, device_code)
        self.seedr = None
        self.load_token()

    def load_token(self):
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                token = f.read().strip()
            self.seedr = Seedr(token=token, callback=self.token_callback)
            print("Loaded Seedr token and initialized Seedr client.")

    def save_token(self, token):
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
        print("Saved Seedr token.")

    def token_callback(self, updated_token):
        self.save_token(updated_token)
        print("Token refreshed and saved.")

    async def start_auth(self, user_id):
        login = Login()
        device_code_data = login.getDeviceCode()
        self.pending_auth[user_id] = (login, device_code_data['device_code'])
        return device_code_data

    async def complete_auth(self, user_id):
        if user_id not in self.pending_auth:
            return False, "No pending authorization. Use /auth first."
        login, device_code = self.pending_auth[user_id]
        try:
            login.authorize(device_code)
            token = login.token
            self.seedr = Seedr(token=token, callback=self.token_callback)
            self.save_token(token)
            del self.pending_auth[user_id]
            return True, "Device authorized! You can now use Seedr commands."
        except Exception as e:
            return False, f"Authorization failed: {e}"

bot = SeedrBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the Seedr Bot!\n"
        "Use /auth to link your Seedr.cc account."
    )

async def auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = await bot.start_auth(user_id)
    msg = (
        "🔑 *Seedr Device Authorization*\n\n"
        "1. Visit: https://seedr.cc/devices\n"
        f"2. Enter this code: `{data['user_code']}`\n"
        "3. Click Authorize.\n"
        "4. Return here and send /complete_auth"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def complete_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    success, message = await bot.complete_auth(user_id)
    await update.message.reply_text(message)

async def my_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot.seedr:
        await update.message.reply_text("Please authorize first using /auth.")
        return
    try:
        files = bot.seedr.listContents()
        if not files['folders'] and not files['files']:
            await update.message.reply_text("Your Seedr is empty.")
            return
        msg = "📂 *Your Seedr Files:*\n"
        for folder in files['folders']:
            msg += f"📁 {folder['name']}\n"
        for file in files['files']:
            msg += f"📄 {file['name']} ({file['size'] // 1024} KB)\n"
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Failed to fetch files: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token("YOUR_TELEGRAM_BOT_TOKEN").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("auth", auth))
    app.add_handler(CommandHandler("complete_auth", complete_auth))
    app.add_handler(CommandHandler("myfiles", my_files))
    print("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()
