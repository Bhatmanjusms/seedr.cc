from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot.config import TELEGRAM_TOKEN
from bot.handlers import start, list_files, get_link, delete_item

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("authorize", authorize))
    app.add_handler(CommandHandler("list", list_files))
    app.add_handler(CommandHandler("getlink", get_link))
    app.add_handler(CommandHandler("delete", delete_item))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), add_magnet))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
