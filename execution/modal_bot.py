import os
import json
import asyncio
import modal
from datetime import datetime
from fastapi import FastAPI, Request

# Define the Modal App
app = modal.App("telegram-lead-gen-bot")

# Define the image with all dependencies
image = (
    modal.Image.debian_slim()
    .pip_install(
        "python-telegram-bot",
        "google-genai",
        "pyairtable",
        "playwright",
        "pandas",
        "python-dotenv",
        "fastapi"
    )
    .run_commands("playwright install chromium")
    .run_commands("playwright install-deps chromium")
)

# Function to process intent with Gemini
@app.function(image=image, secrets=[modal.Secret.from_name("bot-secrets")])
async def process_intent(user_text):
    from google import genai
    import json
    import os
    
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    
    SYSTEM_PROMPT = """
    You are a friendly, professional AI Lead Generation Expert. 
    Your goal is to chat with the user and help them with their lead generation needs.

    YOU HAVE TWO MODES:
    1. CHAT: For greetings, small talk, explaining what you can do, or answering general questions.
    2. WORKFLOW: When the user explicitly asks to find new leads (SCRAPE) or search their database (SEARCH).

    POSSIBLE ACTIONS:
    - "SCRAPE": User wants to find NEW leads from Google Maps (e.g., "Find 10 plumbers in New York").
      Params: {"service": string, "city": string, "count": integer}
    - "SEARCH": User wants to search their EXISTING database (e.g., "Look up landscapers in Miami").
      Params: {"service": string, "city": string, "count": integer}
    - "CHAT": Use this for everything else.

    DIRECTIONS:
    - Always be helpful and conversational.
    - If you trigger a SCRAPE or SEARCH action, include a conversational "reply" telling them what you're doing.
    - If it's just a "CHAT" action, put your entire response in the "reply" field.

    OUTPUT FORMAT:
    Return ONLY a JSON object. No markdown formatting. Example:
    {"action": "SCRAPE", "params": {"service": "plumbers", "city": "Miami", "count": 5}, "reply": "Sure! I'll find 5 plumbers in Miami for you."}
    """
    try:
        prompt = f"{SYSTEM_PROMPT}\n\nUser Message: {user_text}"
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        raw_text = response.text.strip().replace('```json', '').replace('```', '')
        result = json.loads(raw_text)
        
        # Ensure 'reply' always exists
        if "reply" not in result:
            result["reply"] = "I'm on it! Let's see what I can do."
        return result
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {"action": "CHAT", "reply": "I'm having a bit of trouble processing that. Could you try again?"}

# Function to scrape Google Maps
@app.function(image=image, timeout=600)
async def scrape_leads(service, city, count):
    from playwright.async_api import async_playwright
    import asyncio
    
    count = int(count)
    leads = []
    search_query = f"{service} in {city}"
    # Use a slightly different URL format that sometimes bypasses redirects
    url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}?hl=en"
    
    print(f"Scraping {count} leads for {search_query}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Randomize user agent slightly
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            print(f"Navigating to {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Check for cookie consent - this is the most common blocker on Modal/Datacenters
            try:
                # Common Google consent buttons
                buttons = await page.query_selector_all('button')
                for btn in buttons:
                    text = await btn.inner_text()
                    if any(word in text.lower() for word in ['agree', 'accept', 'allow all']):
                        print(f"Found consent button: '{text}'. Clicking...")
                        await btn.click()
                        await asyncio.sleep(3)
                        break
            except:
                pass

            # Wait for content
            print("Waiting for results list...")
            # Results are either in a feed or articles
            try:
                await page.wait_for_selector('div[role="feed"], div[role="article"], .qBF1Pd', timeout=20000)
            except:
                print("Primary selectors not found. Checking page content...")
                body_text = await page.inner_text("body")
                if "unusual traffic" in body_text.lower():
                    print("🚨 Google detected unusual traffic (CAPTCHA).")
                    return []
                print(f"Page Title: {await page.title()}")
                # If we see results but not the feed, we might be on a direct business page
                if await page.query_selector('.qBF1Pd'):
                    print("Found direct result.")
                else:
                    return []

            while len(leads) < count:
                # Find results
                entries = await page.query_selector_all('div[role="article"]')
                if not entries:
                    # Try fallback selector for results
                    entries = await page.query_selector_all('div.Nv2Ybe, div.UaMe90')
                
                print(f"Page has {len(entries)} entries.")
                
                for entry in entries:
                    if len(leads) >= count: break
                    try:
                        # Extract Name
                        name_el = await entry.query_selector('.qBF1Pd, .fontHeadlineSmall, h3')
                        name = await name_el.inner_text() if name_el else "N/A"
                        if name == "N/A" or any(l['name'] == name for l in leads): continue
                        
                        # Extract Rating
                        rating = "N/A"
                        rating_el = await entry.query_selector('.MW4etd, .MW4v7d, span[aria-label*="stars"]')
                        if rating_el: 
                            rating_text = await rating_el.inner_text()
                            if not rating_text: # Try aria-label
                                aria = await rating_el.get_attribute('aria-label')
                                if aria: rating = aria.split(' ')[0]
                            else:
                                rating = rating_text
                        
                        # Extract Address
                        address = "N/A"
                        info_spans = await entry.query_selector_all('.W4Efsd span')
                        for span in info_spans:
                            text = (await span.inner_text()).strip()
                            if any(c.isdigit() for c in text) and len(text) > 8 and not any(k in text.lower() for k in ['open', 'close', '·', 'rating']):
                                address = text
                                break
                        
                        # Extract Website
                        website = "N/A"
                        website_el = await entry.query_selector('a[aria-label*="website"], a[aria-label*="Website"]')
                        if website_el: website = await website_el.get_attribute('href')

                        # Extract Email
                        email = "N/A"
                        if website != "N/A":
                            try:
                                import re
                                site_page = await browser.new_page()
                                await site_page.goto(website, wait_until="domcontentloaded", timeout=15000)
                                mailtos = await site_page.evaluate('''() => {
                                    return Array.from(document.querySelectorAll('a[href^="mailto:"]')).map(a => a.href.replace('mailto:', ''));
                                }''')
                                if mailtos and len(mailtos) > 0:
                                    email = mailtos[0].split('?')[0]
                                else:
                                    content = await site_page.inner_text("body")
                                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                                    emails = re.findall(email_pattern, content)
                                    valid_emails = [e for e in emails if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'))]
                                    if valid_emails:
                                        email = valid_emails[0]
                            except Exception as e:
                                print(f"Error scraping website {website}: {e}")
                            finally:
                                await site_page.close()

                        if website == "N/A" or email == "N/A":
                            print(f"Skipping {name} - Missing website or email.")
                            continue

                        leads.append({
                            "name": name, "service": service, "address": address,
                            "website": website, "email": email, "rating": rating, 
                            "date_created": datetime.now().strftime("%Y-%m-%d"),
                            "status": "lead"
                        })
                        print(f"✅ Found: {name} (Email: {email})")
                    except Exception as e: 
                        continue
                
                if len(leads) < count:
                    # Scroll
                    feed = await page.query_selector('div[role="feed"]')
                    if feed:
                        await feed.evaluate("element => element.scrollBy(0, 1500)")
                        await asyncio.sleep(3)
                    else:
                        break
        except Exception as e:
            print(f"General scraping error: {e}")
        finally:
            await browser.close()
            
    return leads[:int(count)]

# Function to interact with Airtable
@app.function(image=image, secrets=[modal.Secret.from_name("bot-secrets")])
def airtable_action(action_type, data):
    from pyairtable import Api
    import requests
    
    api = Api(os.environ["AIRTABLE_API_KEY"])
    table = api.table(os.environ["AIRTABLE_BASE_ID"], os.environ["AIRTABLE_TABLE_NAME"])
    
    if action_type == "SAVE":
        formatted = []
        for lead in data:
            # Ensure we send clean strings to avoid 'Invalid multiple choice' errors if field is a Select
            formatted.append({
                "Name": str(lead.get("name") or "Unknown"),
                "Service": str(lead.get("service") or "Unknown"),
                "Address": str(lead.get("address") or "N/A"),
                "Website": str(lead.get("website") or "N/A"),
                "Email": str(lead.get("email") or "N/A"),
                "Rating": float(lead.get("rating")) if lead.get("rating") != "N/A" and lead.get("rating") else 0.0,
                "Date Created": lead.get("date_created") or datetime.now().strftime("%Y-%m-%d")
            })
        try:
            print(f"Attempting to save {len(formatted)} leads to Airtable...")
            table.batch_create(formatted)
            print("Successfully saved to Airtable.")
            return True
        except requests.exceptions.HTTPError as e:
            print(f"Airtable HTTP Error: {e.response.text}")
            # If it's a select field error, the user needs to change the column to 'Single Line Text'
            # but we will raise it so the orchestrator knows it failed.
            raise e
        except Exception as e:
            print(f"Airtable Save Error: {e}")
            raise e
    
    elif action_type == "SEARCH":
        try:
            # Clean service name for formula
            svc = data.get('service', '').replace("'", "\\'")
            formula = f"AND({{Service}}='{svc}')"
            records = table.all(formula=formula, sort=["-Rating"], max_records=data.get("count", 5))
            return [{
                "name": r['fields'].get("Name"),
                "rating": r['fields'].get("Rating"),
                "address": r['fields'].get("Address")
            } for r in records]
        except Exception as e:
            print(f"Airtable Search Error: {e}")
            return []

@app.local_entrypoint()
async def test_flow(service="landscapers", city="New York", count=2):
    """Run this with: modal run execution/modal_bot.py"""
    print(f"🚀 Testing Scrape + Airtable flow for {count} {service} in {city}...")
    
    # 1. Scrape
    leads = await scrape_leads.remote.aio(service, city, count)
    if not leads:
        print("❌ Scrape failed to find leads.")
        return
        
    print(f"✅ Scraped {len(leads)} leads.")
    
    # 2. Save
    try:
        airtable_action.remote("SAVE", leads)
        print("✅ Success! Data is in Airtable.")
    except Exception as e:
        print(f"❌ Airtable Save failed: {e}")
        print("\nTIP: If you get 'INVALID_MULTIPLE_CHOICE_OPTIONS', change your 'Service' column in Airtable from 'Single Select' to 'Single line text'.")

# Webhook Handler
@app.function(image=image, secrets=[modal.Secret.from_name("bot-secrets")], timeout=600)
@modal.asgi_app()
def telegram_webhook():
    from telegram import Bot
    web_app = FastAPI()

    @web_app.get("/test-scrape")
    async def test_scrape(service: str = "dentists", city: str = "Miami", count: int = 2):
        leads = await scrape_leads.remote.aio(service, city, count)
        return {"leads": leads}

    @web_app.post("/")
    async def handle_webhook(request: Request):
        try:
            payload = await request.json()
            bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
            
            if "message" in payload:
                chat_id = payload["message"]["chat"]["id"]
                text = payload["message"].get("text", "")
                
                # 1. Process Intent
                decision = await process_intent.remote.aio(text)
                try:
                    await bot.send_message(chat_id=chat_id, text=decision.get("reply", "Processing..."))
                except Exception as e:
                    print(f"Failed to send Telegram reply: {e}")
                
                # 2. Execute Action
                action = decision.get("action")
                params = decision.get("params", {})
                
                if action == "SCRAPE":
                    try:
                        leads = await scrape_leads.remote.aio(params["service"], params["city"], params["count"])
                        if leads:
                            airtable_action.remote("SAVE", leads)
                            preview = "\n".join([f"- {l['name']} ({l['rating']}⭐)" for l in leads[:3]])
                            await bot.send_message(chat_id=chat_id, text=f"✅ Saved {len(leads)} leads to Airtable!\n\nPreview:\n{preview}")
                        else:
                            await bot.send_message(chat_id=chat_id, text="No leads found for that search.")
                    except Exception as e:
                        print(f"Scrape error: {e}")
                        await bot.send_message(chat_id=chat_id, text="Sorry, I hit a snag while scraping.")
                
                elif action == "SEARCH":
                    try:
                        results = airtable_action.remote("SEARCH", params)
                        if results:
                            preview = "\n".join([f"- {r['name']} ({r['rating']}⭐)" for r in results])
                            await bot.send_message(chat_id=chat_id, text=f"Found in database:\n\n{preview}")
                        else:
                            await bot.send_message(chat_id=chat_id, text="No matches found in Airtable.")
                    except Exception as e:
                        print(f"Search error: {e}")
                        await bot.send_message(chat_id=chat_id, text="Error searching the database.")
                        
            return {"status": "ok"}
        except Exception as e:
            print(f"Global Webhook Error: {e}")
            return {"status": "error", "message": str(e)}

    return web_app
