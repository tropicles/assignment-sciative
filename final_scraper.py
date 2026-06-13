from playwright.sync_api import sync_playwright
import pandas as pd
import re

def clean_text(raw_text):
    """Removes HTML tags from a string."""
    if not raw_text:
        return "N/A"
    return re.sub(r'<.*?>', ' ', raw_text).strip()

def parse_tv_data(raw_tv):
    """Extracts specific fields from the raw API dictionary."""
    return {
        'Product_Name': raw_tv.get('name', 'Unknown'),
        'Brand': raw_tv.get('manufacturer', 'Unknown'),
        'Price': raw_tv.get('price', {}).get('value', 0),
        'Rating': raw_tv.get('averageRating', 'Unrated'),
        'Description': clean_text(raw_tv.get('quickViewDesc')),
        'Image_URL': raw_tv.get('plpImage', 'No Image')
    }

def load_all_products(page):
    """Clicks the 'View More' button until all products are loaded."""
    click_count = 0
    while True:
        try:
            view_more_btn = page.locator("button.btn-view-more, button:has-text('View More')").first
            
            if view_more_btn.is_visible(timeout=3000):
                view_more_btn.scroll_into_view_if_needed()
                view_more_btn.click()
                click_count += 1
                print(f"Clicked 'View More' {click_count} times...")
                page.wait_for_timeout(4000)
            else:
                print("End of catalog reached.")
                break
        except Exception:
            print("Finished clicking or button became unclickable.")
            break

def save_to_excel(raw_data, filename):
    """Deduplicates, ranks, and saves the data to an Excel file."""
    unique_tvs = []
    seen_names = set()

    # Process and deduplicate data
    for raw_tv in raw_data:
        tv_info = parse_tv_data(raw_tv)
        
        if tv_info['Product_Name'] not in seen_names:
            unique_tvs.append(tv_info)
            seen_names.add(tv_info['Product_Name'])

    # Apply Catalog Ranking
    for index, tv in enumerate(unique_tvs):
        tv['Catalog_Ranking'] = index + 1

    # Export to Excel
    df = pd.DataFrame(unique_tvs)
    column_order = ['Catalog_Ranking', 'Product_Name', 'Brand', 'Price', 'Rating', 'Description', 'Image_URL']
    
    df[column_order].to_excel(filename, index=False)
    print(f"Successfully saved {len(unique_tvs)} unique TVs to {filename}.")

def main():
    url = "https://www.croma.com/televisions-accessories/c/997?q=%3Arelevance"
    intercepted_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        def handle_response(response):
            """Silently intercepts API requests to grab JSON data."""
            if "search" in response.url or "croma/products" in response.url:
                try:
                    data = response.json()
                    # Chain .get() methods to safely navigate the JSON hierarchy
                    new_tvs = data.get('plpData', {}).get('products', data.get('products', []))
                    
                    if new_tvs:
                        intercepted_data.extend(new_tvs)
                        print(f"--> Intercepted {len(new_tvs)} TVs!")
                except Exception:
                    pass

        # Attach the listener
        page.on("response", handle_response)
        
        print("Loading initial page...")
        page.goto(url, timeout=60000)
        page.wait_for_timeout(5000) 
        
        print("Scrolling and loading catalog...")
        load_all_products(page)
        
        browser.close()

    print("Processing data...")
    save_to_excel(intercepted_data, 'Croma_LED_TVs_Complete.xlsx')

if __name__ == "__main__":
    main()