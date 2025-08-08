import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import json
import datetime

# --- Google Sheets Setup ---
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open("Knox Orders").sheet1
    return sheet

# --- Telegram Bot Handlers ---
def start(update, context):
    # This could be expanded to provide more info
    update.message.reply_text('Welcome to the Knox Bundles bot!')

def handle_webapp_data(update, context):
    data = json.loads(update.message.web_app_data.data)
    sheet = get_sheet()
    
    # Append order to Google Sheet
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payment_ref = f"KNOX{int(datetime.datetime.now().timestamp())}"
    row = [timestamp, payment_ref, data['name'], data['contact'], data['bundle'], data['price'], 'Pending']
    sheet.append_row(row)
    
    # Send payment instructions
    payment_message = f"""
    Thank you for your order, {data['name']}!

    **Payment Instructions**
    ------------------------
    Bundle: {data['bundle']}
    Price: {data['price']}
    
    Please make payment to one of the following:
    - Bank: [Your Bank Details]
    - PayPal: [Your PayPal Link]
    
    **IMPORTANT:** Use this reference ID in your payment description:
    `{payment_ref}`
    
    After payment, an admin will confirm it shortly.
    """
    update.message.reply_text(payment_message, parse_mode='Markdown')

def orders(update, context):
    if str(update.message.chat_id) == os.environ['ADMIN_CHAT_ID']:
        sheet = get_sheet()
        records = sheet.get_all_records()[-5:] # Get last 5 orders
        if not records:
            update.message.reply_text("No recent orders.")
            return
        
        message = "**Recent Orders**\n------------------\n"
        for record in records:
            message += f"Ref: `{record['Payment Ref']}`\nName: {record['Name']}\nBundle: {record['Bundle']}\nStatus: {record['Status']}\n\n"
        update.message.reply_text(message, parse_mode='Markdown')

def confirm(update, context):
    if str(update.message.chat_id) == os.environ['ADMIN_CHAT_ID']:
        if not context.args:
            update.message.reply_text("Please provide a payment reference. Usage: /confirm <ref>")
            return
        
        payment_ref = context.args[0]
        sheet = get_sheet()
        try:
            cell = sheet.find(payment_ref)
            sheet.update_cell(cell.row, 7, "Confirmed") # Update status to Confirmed
            update.message.reply_text(f"Order `{payment_ref}` has been marked as confirmed.", parse_mode='Markdown')
        except gspread.exceptions.CellNotFound:
            update.message.reply_text(f"Order with reference `{payment_ref}` not found.", parse_mode='Markdown')


def main():
    updater = Updater(os.environ['TELEGRAM_TOKEN'], use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("orders", orders))
    dp.add_handler(CommandHandler("confirm", confirm))
    dp.add_handler(MessageHandler(Filters.status_update.web_app_data, handle_webapp_data))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
