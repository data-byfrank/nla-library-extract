import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urljoin
import re

PAGE_SIZE = 100
SLEEP_BETWEEN_PAGES = 1.5
MAX_RETRIES = 3
OUTPUT_FILE = "libraries_list.csv"
BASE_URL = "https://www.nla.gov.au/apps/libraries/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:137.0) Gecko/20100101 Firefox/137.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.nla.gov.au",
    "Connection": "keep-alive",
    "Referer": "https://www.nla.gov.au/apps/libraries/",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Priority": "u=0, i",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

BASE_PAYLOAD = {
    "libtype": "All",
    "termtype": "Keyword",
    "dosearch": "Search",
    "action": "LibSearch",
    "libname": "",
    "libstate": "Australia-wide",
    "chunk": PAGE_SIZE
}

def save_data_to_csv(data, columns):
    df = pd.DataFrame(data, columns=columns)
    uneeded_columns = ["Location", "Details", "Web catalogue", "Telnet catalogue"]
    df = df.drop(columns=[col for col in uneeded_columns if col in df.columns], errors='ignore')
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(data)} rows to CSV.")

def get_address(session, url, headers):
    try:
        resp = session.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        address_strong = soup.find("strong", string=lambda text: text and "Library's street address" in text)
        address_parent = address_strong.find_parent("p") if address_strong else None
        if address_parent:
            address_lines = list(address_parent.stripped_strings)[1:]  # skip label
            address = " ".join(part.strip() for part in address_lines)
            address = address.replace("\n", " ").replace("\r", " ").strip()
            address = address.replace("(see also location map ) ", "").strip()
            address = re.sub(r"\s+", " ", address)
            return address
    except Exception as e:
        print(f"Failed to get address: {e}")
    return ""

def main():
    session = requests.Session()

    # Initial GET to set up session/cookies
    init_response = session.get(BASE_URL, headers=HEADERS)
    if init_response.status_code != 200:
        raise Exception(f"Failed to load initial page. Status code: {init_response.status_code}")

    # Initial POST to set cookies
    response = session.post(BASE_URL, data=BASE_PAYLOAD, headers=HEADERS, timeout=10)
    if response.status_code != 200:
        raise Exception(f"Failed to execute first post. Status code: {response.status_code}")

    all_data = []
    headers_list = []
    page = 1

    while True:
        print(f"Scraping page {page}...")
        payload = BASE_PAYLOAD.copy()
        payload["chunk"] = page
        payload["mode"] = "display"

        success = False
        for attempt in range(MAX_RETRIES):
            try:
                response = session.post(BASE_URL, data=payload, headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    success = True
                    break
                else:
                    print(f"Status code {response.status_code} on attempt {attempt+1}")
            except requests.RequestException as e:
                print(f"Request failed: {e} (attempt {attempt+1})")
            time.sleep(2)

        if not success:
            print(f"Failed to retrieve page {page} after {MAX_RETRIES} attempts. Exiting.")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="summary")
        if not table:
            print("No more data found or empty table.")
            break

        # Extract headers only once
        if page == 1:
            headers_row = table.find("tr")
            headers_list = [th.get_text(strip=True) for th in headers_row.find_all("th")]
            rename_map = {
                "Library": "Name",
                "Parent organisation": "ParentOrg",
            }
            headers_list = [rename_map.get(h, h) for h in headers_list]
            headers_list.append("OrgID")
            headers_list.append("Address")

        # Extract data rows
        rows = table.find_all("tr")[1:]  # Skip header row
        for row in rows:
            cols = [re.sub(r'\s+', ' ', td.get_text(strip=True)) for td in row.find_all("td")]
            if not cols:
                continue
            details_image = row.find("img", alt="[More details for this library]")
            details_parent = details_image.find_parent("a") if details_image else None
            OrgID = ""
            address = ""
            if details_parent and details_parent.has_attr("href"):
                details_url = details_parent["href"]
                OrgID = details_url.split("=")[-1] if "=" in details_url else ""
                full_url = urljoin(BASE_URL, details_url)
                time.sleep(0.1)
                address = get_address(session, full_url, HEADERS)
                if not address:
                    print("Address not found.")
            cols.append(OrgID)
            cols.append(address)
            all_data.append(cols)

        save_data_to_csv(all_data, headers_list)
        page += 1
        time.sleep(SLEEP_BETWEEN_PAGES)

    if all_data:
        save_data_to_csv(all_data, headers_list)
    print("Scraping complete.")

if __name__ == "__main__":
    main()
