import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# Logging
logging.basicConfig(level=logging.INFO)

# Google Drive setup
def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        "service_account.json",
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a file (max 2GB) to upload to Google Drive.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.effective_attachment.get_file()
    file_name = update.message.effective_attachment.file_name or "uploaded_file"
    file_path = os.path.join("downloads", file_name)

    os.makedirs("downloads", exist_ok=True)
    await file.download_to_drive(file_path)
    await update.message.reply_text("Uploading to Google Drive...")

    drive_service = get_drive_service()
    file_metadata = {"name": file_name}
    media = MediaFileUpload(file_path, resumable=True)

    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink"
    ).execute()

    await update.message.reply_text(f"Upload complete! [View File]({uploaded_file['webViewLink']})", parse_mode="Markdown")
    os.remove(file_path)

# Bot init
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL | filters.Video.ALL | filters.Audio.ALL, handle_file))

app.run_polling()
