from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot.handlers import start, handle_magnet, list_files, delete_file, get_link
from bot.config import TELEGRAM_TOKEN

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("list", list_files))
app.add_handler(CommandHandler("delete", delete_file))
app.add_handler(CommandHandler("get", get_link))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_magnet))

if __name__ == "__main__":
    print("🚀 Bot is running...")
    app.run_polling()
