# Workflow: Search Leads in Airtable

## Description
This workflow queries the Airtable database to find leads based on specific filtering criteria.

## Input Parameters
- `service` (string, optional): The type of business (e.g., "plumbers").
- `city` (string, optional): The city/location.
- `min_rating` (float, optional): The minimum rating required (0.0 to 5.0).
- `status` (string, optional): The status of the lead (e.g., "lead").
- `count` (int, default=5): The maximum number of results to return.

## Logic
1. Initialize the Airtable client using the `AIRTABLE_API_KEY` from environment variables.
2. Build a filter formula using Airtable's formula syntax (e.g., `AND({Rating} >= 4, {City} = 'Miami')`).
3. Query the table with the filter and a sort configuration (`Rating` field, descending).
4. Limit the results to the requested `count`.
5. Format the returned records into a clean list of leads.

## Output
- A list of matching lead dictionaries, sorted by rating.
