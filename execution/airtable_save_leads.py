import os
import csv
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def airtable_save_leads(leads, base_id, table_name):
    """
    Saves a list of leads to Airtable.
    """
    api_key = os.getenv("AIRTABLE_API_KEY")
    if not api_key:
        print("Error: AIRTABLE_API_KEY not found in .env")
        return False
    
    if not base_id or not table_name:
        print("Error: Base ID or Table Name is missing.")
        return False

    api = Api(api_key)
    table = api.table(base_id, table_name)
    
    # Format leads for Airtable (PyAirtable expects list of dicts)
    # The keys in the dict must match the Column Names in Airtable exactly
    formatted_records = []
    for lead in leads:
        # Map fields to Airtable Column Names (Capitalized as is standard)
        record = {
            "Name": lead.get("name"),
            "Service": lead.get("service"),
            "Address": lead.get("address"),
            "Website": lead.get("website"),
            "Rating": float(lead.get("rating")) if lead.get("rating") != "N/A" else 0,
            "Date Created": lead.get("date_created"),
            # "Status": lead.get("status", "lead")
        }
        formatted_records.append(record)

    try:
        print(f"Uploading {len(formatted_records)} records to Airtable...")
        # PyAirtable handle batching automatically
        table.batch_create(formatted_records)
        print("Successfully saved leads to Airtable.")
        return True
    except Exception as e:
        print(f"Error saving to Airtable: {e}")
        return False

if __name__ == "__main__":
    # Test logic: Load from the .tmp/test_leads.csv we just created
    import pandas as pd
    
    CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".tmp", "test_leads.csv"))
    BASE_ID = os.getenv("AIRTABLE_BASE_ID") # Set this in your .env
    TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME") # Set this in your .env

    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        leads = df.to_dict('records')
        
        if BASE_ID and TABLE_NAME:
            airtable_save_leads(leads, BASE_ID, TABLE_NAME)
        else:
            print("Skipping upload: AIRTABLE_BASE_ID or AIRTABLE_TABLE_NAME not set in .env")
            print("Leads loaded from CSV:")
            for l in leads:
                print(f"- {l['name']}")
    else:
        print(f"Test CSV not found at {CSV_PATH}. Run the scraper first.")
