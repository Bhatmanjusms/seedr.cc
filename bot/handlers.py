from telegram import Update
from telegram.ext import ContextTypes
from .seedr_api import SeedrAPI

# Dictionary to store user sessions
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    seedr = SeedrAPI()
    device_data = seedr.get_device_code()
    user_sessions[user_id] = {
        "seedr": seedr,
        "device_code": device_data["device_code"],
        "interval": device_data.get("interval", 5)
    }
    await update.message.reply_text(
        f"Please visit {device_data['verification_url']} and enter the code: {device_data['user_code']}\n"
        "After authorizing, send /authorize to complete the process."
    )

async def auth_command(update, context):
    user_id = update.effective_user.id
    
    auth_data = await bot.start_device_auth(user_id)
    if auth_data:
        message = f"""
🔐 **Device Authorization Required**

1. Go to: {auth_data['verification_url']}
2. Enter this code: `{auth_data['user_code']}`
3. Click "Authorize Device"
4. Send /complete_auth when done
        """
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Failed to generate authorization code. Please try again.")

async def complete_auth_command(update, context):
    user_id = update.effective_user.id
    
    success = await bot.complete_auth(user_id)
    if success:
        await update.message.reply_text("✅ Device authorized successfully! You can now use Seedr features.")
    else:
        await update.message.reply_text("❌ Authorization failed. Make sure you completed the steps on the website.")


async def add_magnet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if not session or not session["seedr"].access_token:
        await update.message.reply_text("Please authorize first using /start and /authorize.")
        return
    magnet_link = update.message.text.strip()
    if not magnet_link.startswith("magnet:"):
        await update.message.reply_text("Please send a valid magnet link.")
        return
    response = session["seedr"].add_torrent(magnet_link)
    if "error" in response:
        await update.message.reply_text(f"Error: {response['error']}")
    else:
        await update.message.reply_text("Magnet link added successfully.")

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if not session or not session["seedr"].access_token:
        await update.message.reply_text("Please authorize first using /start and /authorize.")
        return
    contents = session["seedr"].list_contents()
    message = "Files:\n"
    for file in contents.get("files", []):
        message += f"{file['id']}: {file['name']} ({file['size'] // (1024 * 1024)} MB)\n"
    for folder in contents.get("folders", []):
        message += f"{folder['id']}: {folder['name']} (Folder)\n"
    await update.message.reply_text(message)

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if not session or not session["seedr"].access_token:
        await update.message.reply_text("Please authorize first using /start and /authorize.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("Please provide the item ID. Usage: /getlink <item_id>")
        return
    item_id = args[0]
    link = session["seedr"].get_download_link(item_id)
    if link:
        await update.message.reply_text(f"Download link: {link}")
    else:
        await update.message.reply_text("Item not found.")

async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if not session or not session["seedr"].access_token:
        await update.message.reply_text("Please authorize first using /start and /authorize.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("Please provide the item ID. Usage: /delete <item_id>")
        return
    item_id = args[0]
    response = session["seedr"].delete_item(item_id)
    if "error" in response:
        await update.message.reply_text(f"Error: {response['error']}")
    else:
        await update.message.reply_text("Item deleted successfully.")
