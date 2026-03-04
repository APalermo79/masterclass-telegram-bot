# Workflow: Scrape Google Maps

## Description
This workflow searches for businesses on Google Maps based on a service and location, then extracts lead details.

## Input Parameters
- `service` (string): The type of business (e.g., "Plumbers", "Coffee Shops").
- `city` (string): The city and/or state to search in (e.g., "Miami", "Toronto").
- `count` (int): The exact number of leads to return.

## Logic
1. Construct a Google Maps search URL: `https://www.google.com/maps/search/{service}+in+{city}`.
2. Navigate to the URL using a headless browser.
3. Scroll and load results until the requested `count` is met.
4. Extract the following fields for each business:
    - `name`
    - `service` (use the input service)
    - `address`
    - `website`
    - `email`
    - `rating`
    - `date_created` (current timestamp)
    - `status` (default to "lead")
5. Ensure exactly `count` items are returned.

## Output
- A list of dictionaries containing lead data.
- Can be saved to a `.csv` file for testing.
