from telegram import Update
from telegram.ext import ContextTypes
from bot.seedr_api import SeedrAPI
import re

# Store user sessions
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message and instructions"""
    welcome_text = """
🌱 **Welcome to Seedr Telegram Bot!**

**Get Started:**
1. `/authorize username password` - Login to your Seedr account
2. Send me any magnet link to start downloading
3. Use `/list` to see your files

**Commands:**
• `/list` - Show your files and folders
• `/getlink <file_id>` - Get download link
• `/delete <file_id>` - Delete a file

**Example:**
`/authorize john.doe mypassword123`

Then send any magnet link like:
`magnet:?xt=urn:btih:...`

🔒 **Privacy:** Your credentials are only used for authentication and are never stored.
    """
    await update.message.reply_text(welcome_text.strip())

async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Authenticate with Seedr using username and password"""
    user_id = update.effective_user.id
    
    # Check if user provided credentials
    if not context.args or len(context.args) < 2:
        help_message = """
❌ **Please provide your Seedr credentials:**

Usage: `/authorize username password`

Example: `/authorize myusername mypassword`

⚠️ **Security:** Your credentials are only used for authentication and are not stored.
        """
        await update.message.reply_text(help_message.strip())
        return
    
    username = context.args[0]
    password = " ".join(context.args[1:])  # In case password has spaces
    
    # Send "logging in" message
    login_msg = await update.message.reply_text("🔄 Logging in to Seedr...")
    
    try:
        seedr = SeedrAPI()
        token = seedr.login_with_credentials(username, password)
        
        user_sessions[user_id] = {
            "seedr": seedr,
            "authorized": True,
            "username": username  # Store for reference
        }
        
        await login_msg.edit_text("✅ Login successful! You can now use the bot.")
        
        # Test the connection by getting account info
        try:
            contents = seedr.list_contents()
            file_count = len(contents.get("files", []))
            folder_count = len(contents.get("folders", []))
            await update.message.reply_text(
                f"📊 **Account Status:**\n"
                f"Files: {file_count}\n"
                f"Folders: {folder_count}\n\n"
                f"Ready to use! Send me a magnet link or use /list to see your files."
            )
        except:
            # Connection test failed, but login might still work
            pass
        
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            error_msg = "Invalid credentials or Seedr API endpoint changed"
        elif "403" in error_msg:
            error_msg = "Access denied - check your username and password"
        elif "timeout" in error_msg.lower():
            error_msg = "Connection timeout - please try again"
        
        await login_msg.edit_text(f"❌ Login failed: {error_msg}")
        
        # Provide troubleshooting help
        help_text = """
🔧 **Troubleshooting:**
• Double-check your username and password
• Make sure your Seedr account is active
• Try again in a few minutes if server is busy
• Contact @yourbotusername if problems persist
        """
        await update.message.reply_text(help_text.strip())

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
