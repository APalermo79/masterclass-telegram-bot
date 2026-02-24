import asyncio
import os
from dotenv import load_dotenv
from execution.scrape_google_maps import scrape_google_maps
from execution.airtable_save_leads import airtable_save_leads

load_dotenv()

async def main():
    service = "plumbers"
    city = "Miami"
    count = 5
    
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_name = os.getenv("AIRTABLE_TABLE_NAME")
    
    print(f"--- Step 1: Scraping {count} {service} in {city} ---")
    leads = await scrape_google_maps(service, city, count)
    
    if not leads:
        print("No leads found. Aborting.")
        return

    print(f"\n--- Step 2: Saving {len(leads)} leads to Airtable ({table_name}) ---")
    success = airtable_save_leads(leads, base_id, table_name)
    
    if success:
        print("\nSUCCESS: All plumbers saved to Airtable.")
    else:
        print("\nFAILURE: Could not save to Airtable.")

if __name__ == "__main__":
    asyncio.run(main())
