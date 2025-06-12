import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Send me a Solana token mint address to see how many *new wallets* bought it and their *total value in USD*.")

def get_token_transfers(mint):
    url = f"https://api.helius.xyz/v0/addresses/{mint}/transactions?api-key={HELIUS_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API error: {e}")
        return []

def get_sol_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
    try:
        response = requests.get(url)
        return response.json().get("solana", {}).get("usd", 0)
    except:
        return 0

def analyze_transfers(transactions, mint):
    new_wallets = set()
    total_amount = 0.0

    for tx in transactions:
        for transfer in tx.get("tokenTransfers", []):
            if transfer.get("mint") == mint:
                to_wallet = transfer.get("toUserAccount")
                if to_wallet not in new_wallets:
                    new_wallets.add(to_wallet)
                    total_amount += float(transfer.get("tokenAmount", {}).get("uiAmount", 0))

    return len(new_wallets), total_amount

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mint = update.message.text.strip()
    await update.message.reply_text("🔍 Analyzing... please wait.")
    
    transactions = get_token_transfers(mint)
    if not transactions:
        await update.message.reply_text("⚠️ Could not fetch data. Check the mint address.")
        return
    
    wallet_count, total_amount = analyze_transfers(transactions, mint)
    sol_price = get_sol_price()
    total_usd = round(total_amount * sol_price, 2)

    await update.message.reply_text(
        f"✅ *New Wallets*: {wallet_count}\n"
        f"💰 *Total Bought*: ${total_usd:,} USD",
        parse_mode="Markdown"
    )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
