import requests

# Replace with your actual HubSpot access token
ACCESS_TOKEN = "pat-na2-9a92dd2d-66bf-46f2-abe0-2b862368c823"

# HubSpot API base
BASE_URL = "https://api.hubapi.com"

# Optional: Specify properties to fetch (limit to a few for testing)
params = {
    "limit": 5,
    "properties": ["dealname", "amount", "dealstage"],
}

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

def fetch_deals():
    url = f"{BASE_URL}/crm/v3/objects/deals"

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        deals = response.json().get("results", [])
        print(f"\n✅ Successfully fetched {len(deals)} deals:\n")
        for deal in deals:
            print(f"ID: {deal['id']}, Name: {deal['properties'].get('dealname')}, Amount: {deal['properties'].get('amount')}")
    else:
        print(f"\n❌ Error fetching deals: {response.status_code}")
        print("Response:", response.text)

if __name__ == "__main__":
    fetch_deals()
