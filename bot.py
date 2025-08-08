import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import json
import datetime
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# --- Google Sheets Setup ---
def get_sheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
                 "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open("Knox Orders").sheet1
        return sheet
    except Exception as e:
        logger.error(f"Error accessing Google Sheet: {e}")
        return None

# --- Telegram Bot Handlers (async versions) ---
async def start(update, context):
    await update.message.reply_text('Welcome to the Knox Bundles bot! Use the menu button to start an order.')

async def handle_webapp_data(update, context):
    logger.info("Received web app data")
    data = json.loads(update.message.web_app_data.data)
    sheet = get_sheet()

    if sheet is None:
        await update.message.reply_text("Sorry, there was an error connecting to the order database. Please try again later.")
        return

    # Append order to Google Sheet
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payment_ref = f"KNOX{int(datetime.datetime.now().timestamp())}"
    row = [timestamp, payment_ref, data.get('name'), data.get('contact'), data.get('bundle'), data.get('price'), 'Pending']
    sheet.append_row(row)

    # Send payment instructions
    payment_message = f"""
Thank you for your order, {data.get('name')}!

**Payment Instructions**
------------------------
Bundle: {data.get('bundle')}
Price: {data.get('price')}

Please make payment to one of the following:
- Bank: [Your Bank Details]
- PayPal: [Your PayPal Link]

**IMPORTANT:** Use this reference ID in your payment description:
`{payment_ref}`

After payment, an admin will confirm it shortly.
"""
    await update.message.reply_text(payment_message, parse_mode='Markdown')

async def orders(update, context):
    if str(update.message.chat_id) != os.environ.get('ADMIN_CHAT_ID'):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    sheet = get_sheet()
    if sheet is None:
        await update.message.reply_text("Could not connect to the order database.")
        return
        
    records = sheet.get_all_records()[-5:]  # Get last 5 orders
    if not records:
        await update.message.reply_text("No recent orders.")
        return

    message = "**Recent Orders**\n------------------\n"
    for record in records:
        message += f"Ref: `{record.get('Payment Ref')}`\nName: {record.get('Name')}\nBundle: {record.get('Bundle')}\nStatus: {record.get('Status')}\n\n"
    await update.message.reply_text(message, parse_mode='Markdown')

async def confirm(update, context):
    if str(update.message.chat_id) != os.environ.get('ADMIN_CHAT_ID'):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Please provide a payment reference. Usage: /confirm <ref>")
        return

    payment_ref = context.args[0]
    sheet = get_sheet()
    if sheet is None:
        await update.message.reply_text("Could not connect to the order database.")
        return
        
    try:
        cell = sheet.find(payment_ref)
        sheet.update_cell(cell.row, 7, "Confirmed")  # Update status to Confirmed
        await update.message.reply_text(f"Order `{payment_ref}` has been marked as confirmed.", parse_mode='Markdown')
    except gspread.exceptions.CellNotFound:
        await update.message.reply_text(f"Order with reference `{payment_ref}` not found.", parse_mode='Markdown')

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.environ['TELEGRAM_TOKEN']).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("orders", orders))
    application.add_handler(CommandHandler("confirm", confirm))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
