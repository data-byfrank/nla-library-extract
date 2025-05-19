import pandas as pd
import requests
import time
from dotenv import load_dotenv
import os

df = pd.read_csv('libraries_list.csv')


load_dotenv
API_KEY= os.getenv("API_KEY")
API_URL = 'https://geocode.maps.co/search'

# Initialize new columns with None values
df['Latitude'] = None
df['Longitude'] = None
df['Geocoder Display Name'] = None

for idx, address in enumerate(df['Address']):
    if pd.notna(df.loc[idx, 'Latitude']):
        print(f"Skipping already processed address: {address}")
        continue  # Skip already processed rows

    params = {
        'q': address,
        'api_key': API_KEY,
    }
    try:
        response = requests.get(API_URL, params=params)
        data = response.json()
        if data:
            result = data[0]
            df.loc[idx, 'Latitude'] = result.get('lat')
            df.loc[idx, 'Longitude'] = result.get('lon')
            df.loc[idx, 'Geocoder Display Name'] = result.get('display_name')
        else:
            df.loc[idx, ['Latitude', 'Longitude', 'Geocoder Display Name']] = [None, None, None]
            print(f"No geocode result for address: {address}")

    except Exception as e:
        print(f"Error geocoding address: {address}\n{e}")
        df.loc[idx, ['Latitude', 'Longitude', 'Geocoder Display Name']] = [None, None, None]

    # Save progress after each row
    df.to_csv('library_details_enriched.csv', index=False)

    time.sleep(1.1)  # Respect rate limits

print("Completed. Enriched data saved to library_details_enriched.csv")
