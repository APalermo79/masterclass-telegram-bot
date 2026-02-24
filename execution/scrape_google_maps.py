import asyncio
import csv
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_google_maps(service, city, count):
    """
    Scrapes Google Maps for a specific service and city.
    Returns exactly 'count' leads.
    """
    print(f"Starting search for {count} {service} in {city}...")
    
    leads = []
    search_query = f"{service} in {city}"
    url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(url)
        # Wait for the results to load
        await page.wait_for_selector('div[role="feed"]', timeout=10000)
        
        while len(leads) < count:
            # Find all result entries
            entries = await page.query_selector_all('div[role="article"]')
            
            for entry in entries:
                if len(leads) >= count:
                    break
                    
                try:
                    # Extract name - Improved selector
                    name_el = await entry.query_selector('.qBF1Pd')
                    name = await name_el.inner_text() if name_el else "N/A"
                    
                    # Avoid duplicates
                    if any(lead['name'] == name for lead in leads):
                        continue
                    
                    # Extract rating - Improved selector and fallback
                    rating = "N/A"
                    # Try direct span first
                    rating_el = await entry.query_selector('.MW4etd, .MW4v7d')
                    if rating_el:
                        rating = await rating_el.inner_text()
                    
                    # Fallback to aria-label parsing
                    if rating == "N/A":
                        rating_container = await entry.query_selector('.ZkP5Je')
                        if rating_container:
                            aria = await rating_container.get_attribute('aria-label')
                            if aria and 'stars' in aria:
                                rating = aria.split('stars')[0].strip()

                    # Extract address - Improved logic
                    address = "N/A"
                    info_spans = await entry.query_selector_all('.W4Efsd span')
                    for span in info_spans:
                        text = (await span.inner_text()).strip()
                        # Address heuristic: 
                        # 1. Contains a number
                        # 2. Longer than 8 chars
                        # 3. Doesn't contain "·" or "review" or "(" 
                        # 4. Doesn't match rating pattern (X.X)
                        if any(char.isdigit() for char in text) and \
                           len(text) > 8 and \
                           not any(kw in text.lower() for kw in ['open', 'close', '·', 'rating', 'review', '(', ')']):
                             address = text
                             break
                    
                    # If heuristic failed, fallback to the second .W4Efsd div if it exists
                    if address == "N/A":
                        info_divs = await entry.query_selector_all('.W4Efsd')
                        if len(info_divs) > 1:
                            text = await info_divs[1].inner_text()
                            if '·' in text:
                                parts = text.split('·')
                                for p in parts:
                                    p_clean = p.strip()
                                    if any(char.isdigit() for char in p_clean) and \
                                       len(p_clean) > 8 and \
                                       '(' not in p_clean:
                                        address = p_clean
                                        break
                    
                    # Extract website - Improved selector
                    website = "N/A"
                    website_el = await entry.query_selector('a[aria-label*="website"], a[aria-label*="Website"]')
                    if website_el:
                        website = await website_el.get_attribute('href')

                    leads.append({
                        "name": name,
                        "service": service,
                        "address": address,
                        "website": website,
                        "rating": rating,
                        "date_created": datetime.now().strftime("%Y-%m-%d"),
                        "status": "lead"
                    })
                    print(f"Found: {name} | Rating: {rating} | Address: {address}")
                    
                except Exception as e:
                    print(f"Error parsing entry: {e}")
                    continue
            
            if len(leads) < count:
                # Scroll down to load more results
                # Target the feed container
                feed = await page.query_selector('div[role="feed"]')
                if feed:
                    await feed.evaluate("element => element.scrollBy(0, 1000)")
                    await asyncio.sleep(2) # Wait for load
                else:
                    break # Cannot scroll further

        await browser.close()
    
    return leads[:count]

def save_to_csv(leads, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    keys = leads[0].keys() if leads else []
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(leads)
    print(f"Saved {len(leads)} leads to {filename}")

if __name__ == "__main__":
    # Test configuration
    TEST_SERVICE = "coffee shops"
    TEST_CITY = "Toronto"
    TEST_COUNT = 2
    OUTPUT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".tmp", "test_leads.csv"))

    # Run the scraper
    results = asyncio.run(scrape_google_maps(TEST_SERVICE, TEST_CITY, TEST_COUNT))
    
    # Save results
    if results:
        save_to_csv(results, OUTPUT_FILE)
    else:
        print("No leads found.")
