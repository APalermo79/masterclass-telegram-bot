# Workflow: Telegram Bot & Gemini Orchestration

## Description
This workflow acts as the "brain" of the system. It receives messages from Telegram, uses Gemini to interpret the user's intent, and routes the request to the appropriate sub-workflow (Scraping or Searching).

## Logic
1.  **Receive Message**: Listen for incoming text via the Telegram Bot API.
2.  **Analyze Intent (Gemini)**:
    *   System Prompt defines three possible actions: `SCRAPE`, `SEARCH`, or `CHAT`.
    *   Gemini extracts parameters: `service`, `city`, `count`, `min_rating`.
3.  **Route and Execute**:
    *   If `SCRAPE`: Call `scrape_google_maps` -> `airtable_save_leads`.
    *   If `SEARCH`: Call `airtable_search_leads`.
    *   If `CHAT`: Reply with a natural, professional response.
4.  **Respond**: Send a formatted message back to the user with the results or confirmation.

## Environment Variables
- `TELEGRAM_BOT_TOKEN`
- `GEMINI_API_KEY`
