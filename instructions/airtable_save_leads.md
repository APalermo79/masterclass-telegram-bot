# Workflow: Save Leads to Airtable

## Description
This workflow takes a list of lead objects and uploads them to a specific Airtable base and table.

## Input Parameters
- `leads` (list of dicts): The lead data extracted from the scraper.
- `base_id` (string): The Airtable Base ID (starts with `app`).
- `table_name` (string): The name of the table (e.g., "Leads").

## Mapping
The script maps the following fields to Airtable columns:
- `name` -> `Name`
- `service` -> `Service`
- `address` -> `Address`
- `website` -> `Website`
- `rating` -> `Rating` (Number/Decimal)
- `date_created` -> `Date Created` (Date)
- `status` -> `Status` (Single Select/String)

## Logic
1. Initialize the Airtable client using the `AIRTABLE_API_KEY` from environment variables.
2. Validate that the base and table are accessible.
3. Batch upload records (Airtable supports up to 10 records per request).
4. Error handling for missing fields or API limits.

## Output
- Confirmation of total records saved.
