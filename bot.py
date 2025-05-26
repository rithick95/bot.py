import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import tempfile

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load your bot token from environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize Google Drive API client using service account
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'service_account.json'  # Make sure this file is in your project folder

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=credentials)

# ID of the Google Drive folder to upload to (optional)
# Share this folder with your service account email!
FOLDER_ID = 'YOUR_GOOGLE_DRIVE_FOLDER_ID'  # Replace with your folder ID or None for root

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Send me any file (up to 2GB), and I'll upload it to Google Drive.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    file_name = file.file_name

    # Download file temporarily
    with tempfile.NamedTemporaryFile(delete=True) as tf:
        file_path = tf.name
        await file.get_file().download_to_drive(custom_path=file_path)

        # Prepare file metadata
        file_metadata = {'name': file_name}
        if FOLDER_ID:
            file_metadata['parents'] = [FOLDER_ID]

        media = MediaFileUpload(file_path, resumable=True)

        # Upload to Google Drive
        drive_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        link = drive_file.get('webViewLink')
        await update.message.reply_text(f"Uploaded to Google Drive: {link}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and update.message:
        await update.message.reply_text('Oops! Something went wrong.')

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_error_handler(error_handler)

    print("Bot started.")
    app.run_polling()

if __name__ == '__main__':
    main()

