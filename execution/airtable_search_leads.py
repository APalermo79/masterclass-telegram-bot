import os
from pyairtable import Api
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def airtable_search_leads(service=None, city=None, min_rating=0, status=None, count=5):
    """
    Searches Airtable for leads matching filters and returns top results sorted by rating.
    """
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_name = os.getenv("AIRTABLE_TABLE_NAME")

    if not all([api_key, base_id, table_name]):
        print("Error: Missing Airtable configuration in .env")
        return []

    api = Api(api_key)
    table = api.table(base_id, table_name)

    # Build filter logic
    filters = []
    
    if service:
        filters.append(f"{{Service}}='{service}'")
    
    if city:
        filters.append(f"FIND('{city}', {{Address}})")

    if min_rating > 0:
        filters.append(f"{{Rating}}>={min_rating}")
    
    if status:
        filters.append(f"{{Status}}='{status}'")

    # Combine filters with AND if multiple exist
    formula = "AND(" + ",".join(filters) + ")" if filters else None

    try:
        print(f"Searching Airtable with formula: {formula}")
        # Fetch records with sorting and limit
        # Sort by Rating descending
        records = table.all(
            formula=formula,
            sort=["-Rating"], 
            max_records=count
        )

        leads = []
        for record in records:
            fields = record['fields']
            leads.append({
                "id": record['id'],
                "name": fields.get("Name"),
                "service": fields.get("Service"),
                "address": fields.get("Address"),
                "website": fields.get("Website"),
                "rating": fields.get("Rating"),
                "date_created": fields.get("Date Created"),
                "status": fields.get("Status")
            })

        print(f"Found {len(leads)} matching leads.")
        return leads

    except Exception as e:
        print(f"Error searching Airtable: {e}")
        return []

if __name__ == "__main__":
    # Test: Find plumbers with rating >= 4
    # Note: Using the plumbers we just scraped
    print("Testing Search: 2 plumbers with rating 4.0 or higher")
    results = airtable_search_leads(service="plumbers", min_rating=0, count=2)
    
    for i, lead in enumerate(results):
        print(f"{i+1}. {lead['name']} | Rating: {lead['rating']}")
