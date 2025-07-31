import os
import csv
import time
import requests
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

def safe_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# ========== CONFIG ==========
EMAIL = "cbig78222@gmail.com"
PASSWORD = "sh3lfS067@fhoq"
HEADLESS = False  # Set to True for headless mode

OUTPUT_DIR = "migration_output"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
CSV_FILE = os.path.join(OUTPUT_DIR, "assets.csv")

BASE_URL = "https://app.shelf.nu"
LOGIN_URL = "https://app.shelf.nu/login"
ASSETS_URL = "https://app.shelf.nu/assets"

# ========== SETUP ==========
os.makedirs(IMAGES_DIR, exist_ok=True)

options = Options()
if HEADLESS:
    options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)

# ========== LOGIN ==========
def login():
    print("Logging in...")
    driver.get(LOGIN_URL)
    time.sleep(2)

    email_input = driver.find_element(By.NAME, "email")
    password_input = driver.find_element(By.NAME, "password")
    email_input.send_keys(EMAIL)
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.RETURN)

    time.sleep(5)
    assert "dashboard" in driver.current_url or "assets" in driver.current_url
    print("Login successful.")

# ========== SCRAPE ASSETS ==========
def scrape_assets():
    driver.get(ASSETS_URL)
    time.sleep(5)

    with open("debug_asset_page.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    assets = []
    page = 1

    while True:
        print(f"Scraping page {page}...")

        asset_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        if not asset_rows:
            print("No assets found on this page.")
            break

        for row in asset_rows:
            try:
                # Image and title via img tag
                img_elem = row.find_element(By.CSS_SELECTOR, "img")
                img_url = img_elem.get_attribute("src")
                title = img_elem.get_attribute("alt").strip()

                # Remaining text columns (td)
                tds = row.find_elements(By.TAG_NAME, "td")
                category = tds[2].text.strip() if len(tds) > 2 else ""
                tags = tds[3].text.strip() if len(tds) > 3 else ""
                custodian = tds[4].text.strip() if len(tds) > 4 else ""
                location = tds[5].text.strip() if len(tds) > 5 else ""

                # Save image
                filename = safe_filename(title) + ".jpg"
                img_path = os.path.join("images", filename)
                full_img_path = os.path.join(IMAGES_DIR, filename)

                if img_url and "https" in img_url:
                    with open(full_img_path, 'wb') as f:
                        f.write(requests.get(img_url).content)

                assets.append({
                    "title": title,
                    "description": "",
                    "categories": category,
                    "tags": tags.replace(",", ";"),
                    "location": location,
                    "custodian": custodian,
                    "image": img_path,
                })

            except Exception as e:
                print(f"Error parsing row: {e}")
                continue

        # Stop here for now — no pagination support yet
        break

    return assets



# ========== WRITE CSV ==========
def write_csv(rows):
    print("Writing CSV...")
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["title", "description", "categories", "tags", "location", "custodian", "image"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

# ========== MAIN ==========
if __name__ == "__main__":
    try:
        login()
        assets = scrape_assets()
        write_csv(assets)
        print(f"Done. Exported {len(assets)} assets to {CSV_FILE}")
    finally:
        driver.quit()

