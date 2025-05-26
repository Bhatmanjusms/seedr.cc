from telegram import Update
from telegram.ext import ContextTypes
from bot.seedr_api import SeedrAPI
import re

# Store user sessions
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message and instructions"""
    welcome_text = """
🌱 Welcome to Seedr Telegram Bot!

Commands:
/authorize - Authenticate with Seedr
/list - List your files
/getlink <file_id> - Get download link
/delete <file_id> - Delete a file

To add torrents, just send me a magnet link after authorization!
    """
    await update.message.reply_text(welcome_text.strip())

async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start OAuth authorization flow"""
    user_id = update.effective_user.id
    
    try:
        # Initialize Seedr API
        seedr = SeedrAPI()
        
        # Get device code
        device_info = seedr.get_device_code()
        device_code = device_info.get("device_code")
        user_code = device_info.get("user_code")
        verification_uri = device_info.get("verification_uri")
        interval = device_info.get("interval", 5)
        
        # Store session info for polling
        user_sessions[user_id] = {
            "seedr": seedr,
            "device_code": device_code,
            "interval": interval,
            "authorized": False
        }
        
        auth_message = f"""
🔐 **Authorization Required**

1. Visit: {verification_uri}
2. Enter code: `{user_code}`
3. Click "Authorize"

I'll automatically detect when you're done!
        """
        
        await update.message.reply_text(auth_message)
        
        # Start polling for token
        try:
            token = seedr.poll_for_token(device_code, interval)
            user_sessions[user_id]["authorized"] = True
            await update.message.reply_text("✅ Authorization successful! You can now use the bot.")
        except Exception as e:
            await update.message.reply_text(f"❌ Authorization failed: {str(e)}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error starting authorization: {str(e)}")

async def add_magnet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add magnet link to Seedr"""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    if not session or not session.get("authorized"):
        await update.message.reply_text("❌ Please authorize first with /authorize")
        return
    
    message_text = update.message.text.strip()
    
    # Check if it's a magnet link
    if not message_text.startswith("magnet:"):
        await update.message.reply_text("❌ Please send a valid magnet link")
        return
    
    try:
        seedr = session["seedr"]
        result = seedr.add_torrent(message_text)
        
        if result.get("result"):
            await update.message.reply_text("✅ Torrent added successfully!")
        else:
            error_msg = result.get("error", "Unknown error")
            await update.message.reply_text(f"❌ Failed to add torrent: {error_msg}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error adding torrent: {str(e)}")

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List files in Seedr account"""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    if not session or not session.get("authorized"):
        await update.message.reply_text("❌ Please authorize first with /authorize")
        return
    
    try:
        seedr = session["seedr"]
        contents = seedr.list_contents()
        
        if not contents:
            await update.message.reply_text("❌ Failed to fetch contents")
            return
        
        files = contents.get("files", [])
        folders = contents.get("folders", [])
        
        if not files and not folders:
            await update.message.reply_text("📁 Your Seedr account is empty")
            return
        
        message_parts = ["📁 **Your Files:**\n"]
        
        # Add folders
        for folder in folders:
            message_parts.append(f"📂 `{folder['id']}` - {folder['name']}")
        
        # Add files
        for file in files:
            size_mb = round(file.get('size', 0) / 1024 / 1024, 2)
            message_parts.append(f"📄 `{file['id']}` - {file['name']} ({size_mb} MB)")
        
        message = "\n".join(message_parts)
        
        # Split message if too long
        if len(message) > 4000:
            message = message[:4000] + "\n... (truncated)"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error listing files: {str(e)}")

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get download link for a file"""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    if not session or not session.get("authorized"):
        await update.message.reply_text("❌ Please authorize first with /authorize")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /getlink <file_id>")
        return
    
    file_id = context.args[0]
    
    try:
        seedr = session["seedr"]
        download_url = seedr.get_download_link(file_id)
        
        if download_url:
            await update.message.reply_text(f"🔗 **Download Link:**\n{download_url}")
        else:
            await update.message.reply_text("❌ File not found or no download link available")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error getting download link: {str(e)}")

async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a file or folder"""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    if not session or not session.get("authorized"):
        await update.message.reply_text("❌ Please authorize first with /authorize")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /delete <file_id>")
        return
    
    file_id = context.args[0]
    
    try:
        seedr = session["seedr"]
        result = seedr.delete_item(file_id)
        
        if result.get("result"):
            await update.message.reply_text("✅ Item deleted successfully!")
        else:
            error_msg = result.get("error", "Unknown error")
            await update.message.reply_text(f"❌ Failed to delete item: {error_msg}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error deleting item: {str(e)}")

# Handle non-command text messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages that aren't commands"""
    message_text = update.message.text.strip()
    
    # Check if it's a magnet link
    if message_text.startswith("magnet:"):
        await add_magnet(update, context)
    else:
        await update.message.reply_text("ℹ️ Send a magnet link to add a torrent, or use /help for commands")
