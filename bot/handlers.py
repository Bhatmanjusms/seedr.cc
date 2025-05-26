from telegram import Update
from telegram.ext import ContextTypes
from seedrcc import Seedr, Login

user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send your Seedr username and password separated by a space.")

async def handle_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        username, password = update.message.text.split()
        seedr_login = Login(username, password)
        token = seedr_login.authorize()
        user_sessions[user_id] = {"seedr": Seedr(token=token)}
        await update.message.reply_text("Login successful! Use /add, /list, etc.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if not session:
        await update.message.reply_text("Please log in first with /start.")
        return
    try:
        contents = session["seedr"].listContents()
        message = "Files:\n" + "\n".join([f"{item['id']}: {item['name']}" for item in contents["files"]])
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")
