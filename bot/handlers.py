from telegram import Update
from telegram.ext import ContextTypes
from .seedr_api import SeedrAPI

api = SeedrAPI()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to Seedr Bot! Send me a magnet link to start downloading.")

async def handle_magnet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    magnet = update.message.text.strip()
    if magnet.startswith("magnet:"):
        resp = api.add_torrent(magnet)
        await update.message.reply_text(f"✅ Added to Seedr: {resp}")
    else:
        await update.message.reply_text("❗️Invalid magnet link.")

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = api.list_files()
    msg = "📂 Files:\n"
    for f in data.get("files", []):
        msg += f"{f['id']}: {f['name']} - {f['size'] // (1024*1024)}MB\n"
    for f in data.get("folders", []):
        msg += f"{f['id']}: {f['name']} (Folder)\n"
    await update.message.reply_text(msg)

async def delete_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.text.strip().split()[-1]
    resp = api.delete_file(file_id)
    await update.message.reply_text(f"🗑️ Deleted: {resp}")

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.text.strip().split()[-1]
    link = api.get_download_link(file_id)
    if link:
        await update.message.reply_text(f"📥 Download Link: {link}")
    else:
        await update.message.reply_text("❗️File not found.")
