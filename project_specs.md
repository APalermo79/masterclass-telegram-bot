# Project Specifications: Telegram Lead Gen Bot

## 1. Input
- User sends a natural language message via Telegram (e.g., "Find 5 plumbers in Miami").
- The system uses Gemini to extract parameters and determine the intended workflow.

## 2. Workflows
- **scrape_google_maps**:
    - Input: `service` (string), `city` (string), `count` (int).
    - Output: A list of `count` leads.
    - Fields: `name`, `service`, `address`, `website`, `rating`, `date_created`, `status` (default: "lead").
- **airtable_save_leads**:
    - Input: List of leads from the scraper.
    - Action: Upload leads to Airtable (using the Airtable API/library).
    - Mapping: Columns must match lead fields exactly.
- **airtable_search_leads**:
    - Input: `city`, `service`, `min_rating`, `status`, `count`.
    - Action: Query Airtable, sort by rating descending.
    - Output: Up to `count` results.

## 3. Tools
- **Telegram**: User interface for input and confirmation.
- **Gemini (Google AI)**: Natural language understanding and workflow orchestration.
- **Airtable**: Primary database for lead storage.
- **Modal**: Serverless deployment platform for hosting the Python scripts and Telegram webhook.
- **Google Maps API (or equivalent scraping tool)**: To fetch local business data.

## 4. Expected Outputs
- Status updates in Telegram (e.g., "Searching for plumbers in Miami...").
- Confirmation of Airtable sync ("Saved 5 leads to Airtable").
- Data preview of top results in the Telegram message.

## 5. Data Storage
- **Airtable**: Persistent storage for all leads.
- **.tmp/**: Local CSV files for intermediate testing data.

## 6. Deployment
- **Platform**: Modal.
- **Security**: All API keys (Telegram, Airtable, Gemini, Google Maps) stored as **Modal Secrets**.
- **Webhooks**: Telegram webhook pointing to the Modal deployment URL.

## 7. Definition of "Done"
- **Test Case**: Send "Find 5 plumbers in Miami" to the bot.
- **Success Criteria**:
    1. 5 leads are correctly scraped and visible in Airtable.
    2. Bot replies: "Done! Saved 5 plumbers in Miami to Airtable."
    3. Bot provides a summary of the top-rated leads in the message.
