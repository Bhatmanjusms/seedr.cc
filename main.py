from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot.config import TELEGRAM_TOKEN
from bot.handlers import start, authorize, list_files, get_link, delete_item, handle_text

def main():
    if not TELEGRAM_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    print("🤖 Starting Seedr Telegram Bot...")
    
    # Create application
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("authorize", authorize))
    app.add_handler(CommandHandler("list", list_files))
    app.add_handler(CommandHandler("getlink", get_link))
    app.add_handler(CommandHandler("delete", delete_item))
    
    # Add message handler for non-command text (magnet links)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

    print("✅ Bot is running and ready to receive messages...")
    print("Press Ctrl+C to stop the bot")
    
    try:
        app.run_polling()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {str(e)}")

if __name__ == "__main__":
    main()
