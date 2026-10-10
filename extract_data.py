import requests
import json

# --- CONFIGURATION ---
API_KEY = "pit-e3565738-9fff-4746-905f-3c8fef9283a8"
LOCATION_ID = "yLiKZKvk2CeI2ckIqd1L"
BASE_URL = "https://services.leadconnectorhq.com"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Version": "2021-07-28",
    "Accept": "application/json"
}

def get_all_contacts():
    print("Fetching all contacts...")
    all_contacts = []
    url = f"{BASE_URL}/contacts/?locationId={LOCATION_ID}&limit=100"
    
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching contacts: {response.text}")
            break
            
        data = response.json()
        contacts = data.get('contacts', [])
        all_contacts.extend(contacts)
        print(f"  -> Fetched {len(contacts)} contacts. Total so far: {len(all_contacts)}")
        
        meta = data.get('meta', {})
        url = meta.get('nextPageUrl')
        
    return all_contacts

def get_all_opportunities():
    print("Fetching all opportunities...")
    all_opportunities = []
    
    # THE FIX: GoHighLevel requires snake_case 'location_id' for this specific endpoint
    url = f"{BASE_URL}/opportunities/search?location_id={LOCATION_ID}&limit=100"
    
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching opportunities: {response.text}")
            break
            
        data = response.json()
        opportunities = data.get('opportunities', [])
        all_opportunities.extend(opportunities)
        print(f"  -> Fetched {len(opportunities)} opportunities. Total so far: {len(all_opportunities)}")
        
        meta = data.get('meta', {})
        url = meta.get('nextPageUrl')
        
    return all_opportunities

# --- EXECUTION ---
print("Starting data extraction...\n")

# 1. Get and Filter Contacts
raw_contacts = get_all_contacts()
print(f"\nTotal raw contacts fetched: {len(raw_contacts)}")

clean_contacts = []
internal_count = 0
no_tag_count = 0

for contact in raw_contacts:
    tags = contact.get('tags', [])
    
    if 'dash-project' in tags:
        if 'internal' not in tags:
            clean_contacts.append(contact)
        else:
            internal_count += 1
    else:
        no_tag_count += 1

print(f"Clean contacts after filtering: {len(clean_contacts)}")
print(f"  -> Excluded {internal_count} contacts tagged as 'internal'")
print(f"  -> Excluded {no_tag_count} contacts missing the 'dash-project' tag")

with open('clean_contacts.json', 'w', encoding='utf-8') as f:
    json.dump(clean_contacts, f, indent=2)

# 2. Get and Filter Opportunities
valid_contact_ids = {c['id'] for c in clean_contacts}
print(f"\nLooking for opportunities linked to these {len(valid_contact_ids)} valid contacts...")

raw_opportunities = get_all_opportunities()
print(f"Total raw opportunities fetched: {len(raw_opportunities)}")

clean_opportunities = []
for opp in raw_opportunities:
    if opp.get('contactId') in valid_contact_ids:
        clean_opportunities.append(opp)

print(f"Clean opportunities linked to our contacts: {len(clean_opportunities)}")

with open('clean_opportunities.json', 'w', encoding='utf-8') as f:
    json.dump(clean_opportunities, f, indent=2)

# 3. Get Pipeline Stages to map IDs to Names
print("\nFetching pipeline stages to map IDs to names...")
pipeline_url = f"{BASE_URL}/opportunities/pipelines?locationId={LOCATION_ID}"
pipeline_response = requests.get(pipeline_url, headers=headers)

if pipeline_response.status_code == 200:
    pipeline_data = pipeline_response.json()
    stages_mapping = {}
    
    # Find the "Sales Pipeline" and extract stage names
    for pipeline in pipeline_data.get('pipelines', []):
        if 'Sales' in pipeline.get('name', ''): # Looks for "Sales Pipeline"
            for stage in pipeline.get('stages', []):
                stages_mapping[stage['id']] = stage['name']
            break # We found it, no need to check other pipelines
            
    with open('pipeline_stages.json', 'w', encoding='utf-8') as f:
        json.dump(stages_mapping, f, indent=2)
    print("Saved pipeline_stages.json")
else:
    print(f"Could not fetch pipeline stages: {pipeline_response.text}")

print("\nSuccess! Check clean_contacts.json and clean_opportunities.json in your folder.")