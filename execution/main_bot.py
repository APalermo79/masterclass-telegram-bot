import os
import json
import asyncio
from google import genai
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

# Import our workflows
from execution.scrape_google_maps import scrape_google_maps
from execution.airtable_save_leads import airtable_save_leads
from execution.airtable_search_leads import airtable_search_leads

load_dotenv()

# Configure Gemini
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are a professional Lead Generation AI assistant. 
Your goal is to understand user requests and return a JSON object representing the intended action.

POSSIBLE ACTIONS:
1. "SCRAPE": User wants to find NEW leads from Google Maps and save them.
   Params: {"service": string, "city": string, "count": integer}
2. "SEARCH": User wants to find EXISTING leads in their database.
   Params: {"service": string, "city": string, "count": integer, "min_rating": float}
3. "CHAT": General conversation or greeting.

OUTPUT FORMAT:
Return ONLY a JSON object. Example:
{"action": "SCRAPE", "params": {"service": "plumbers", "city": "Miami", "count": 5}, "reply": "Sure! I'll find 5 plumbers in Miami for you."}
"""

async def process_message(user_text):
    """Uses Gemini to determine action and parameters."""
    prompt = f"{SYSTEM_PROMPT}\n\nUser Message: {user_text}"
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt
    )
    try:
        # Clean up JSON formatting if any
        raw_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(raw_text)
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        return {"action": "CHAT", "reply": "I'm sorry, I'm having trouble processing that. Could you try rephrasing?"}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.message.chat_id
    
    print(f"Received message: {user_text}")
    
    # 1. Ask Gemini what to do
    decision = await process_message(user_text)
    action = decision.get("action")
    params = decision.get("params", {})
    initial_reply = decision.get("reply", "Processing...")

    await context.bot.send_message(chat_id=chat_id, text=initial_reply)

    # 2. Route to Workflow
    if action == "SCRAPE":
        service = params.get("service")
        city = params.get("city")
        count = params.get("count", 5)
        
        # Run Scraper
        leads = await scrape_google_maps(service, city, count)
        if leads:
            # Save to Airtable
            base_id = os.getenv("AIRTABLE_BASE_ID")
            table_name = os.getenv("AIRTABLE_TABLE_NAME")
            airtable_save_leads(leads, base_id, table_name)
            
            # Format Preview
            preview = "\n".join([f"- {l['name']} ({l['rating']}⭐)" for l in leads[:3]])
            await context.bot.send_message(
                chat_id=chat_id, 
                text=f"✅ Done! Saved {len(leads)} leads to Airtable.\n\nTop Results:\n{preview}"
            )
        else:
            await context.bot.send_message(chat_id=chat_id, text="Sorry, I couldn't find any leads for that search.")

    elif action == "SEARCH":
        results = airtable_search_leads(
            service=params.get("service"),
            city=params.get("city"),
            min_rating=params.get("min_rating", 0),
            count=params.get("count", 5)
        )
        if results:
            preview = "\n".join([f"- {l['name']} ({l['rating']}⭐) | {l['address']}" for l in results])
            await context.bot.send_message(chat_id=chat_id, text=f"Found existing leads in your database:\n\n{preview}")
        else:
            await context.bot.send_message(chat_id=chat_id, text="No matching leads found in your Airtable.")

if __name__ == "__main__":
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found.")
    else:
        print("Bot is starting...")
        application = ApplicationBuilder().token(TOKEN).build()
        
        msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
        application.add_handler(msg_handler)
        
        application.run_polling()
