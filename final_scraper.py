from playwright.sync_api import sync_playwright
import pandas as pd
import json
import re


def remove_html_tags(raw_text):
    """Finds anything between < and > and deletes it."""
    if not raw_text:
        return "N/A"
    # The regex <.*?> means: "Find a '<', then any characters, until the next '>'"
    clean_text = re.sub(r'<.*?>', ' ', raw_text)
    return clean_text.strip()

def extract_json_from_html(html_content):
    """Scans the ugly HTML and cuts out just the JSON dictionary."""
    # The regex looks for our target word, grabs everything after it (.*?), and stops at </script>
    pattern = r'window\.__INITIAL_DATA__=(.*?)</script>'
    match = re.search(pattern, html_content, re.DOTALL)
    
    if match:
        raw_string = match.group(1)
        # JavaScript uses 'undefined', but Python needs 'null'. We swap them here.
        fixed_string = raw_string.replace('undefined', 'null')
        return json.loads(fixed_string)
    
    return None

def get_tv_list(data_dictionary):
    """Navigates step-by-step down the dictionary to find the products list."""
    # Doing this step-by-step is much easier to read than chaining it all on one line
    step1 = data_dictionary.get('plpReducer', {})
    step2 = step1.get('plpData', {})
    tv_list = step2.get('products', [])
    return tv_list

def get_total_pages(data_dictionary):
    """Finds the total number of pages available to scrape."""
    step1 = data_dictionary.get('plpReducer', {})
    step2 = step1.get('plpData', {})
    pagination = step2.get('pagination', {})
    total = pagination.get('totalPages', 1)
    return total



def main():
    base_url = "https://www.croma.com/televisions-accessories/c/997?q=%3Arelevance"
    all_tvs = []
    
    with sync_playwright() as p:
        print("Launching Browser...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        current_page = 0
        total_pages = 1 
        
        while current_page < total_pages:
            # 1. Build the URL for the current page
            page_url = base_url + "&page=" + str(current_page)
            print("Fetching:", page_url)
            
            # 2. Load the page and grab the raw HTML
            response = page.goto(page_url, timeout=60000)
            html = response.text()
            
            # 3. Use our helper function to extract the JSON
            json_data = extract_json_from_html(html)
            
            if json_data:
                # Update total pages if this is our very first time through the loop
                if current_page == 0:
                    total_pages = get_total_pages(json_data)
                    print("Total pages to scrape:", total_pages)
                
                # 4. Use our helper function to get the list of TVs
                products = get_tv_list(json_data)
                print("Found", len(products), "TVs on this page.")
                
                # 5. Loop through the TVs and save them
                for tv in products:
                    # Get the price safely (since price is a dictionary inside the TV dictionary)
                    tv_price = tv.get('price', {})
                    actual_price = tv_price.get('value', 0)
                    
                    tv_info = {
                        'Product_Name': tv.get('name', 'Unknown'),
                        'Brand': tv.get('manufacturer', 'Unknown'),
                        'Price': actual_price,
                        'Rating': tv.get('averageRating', 'Unrated'),
                        'Description': remove_html_tags(tv.get('quickViewDesc')),
                        'Image_URL': tv.get('plpImage', 'No Image')
                    }
                    all_tvs.append(tv_info)
                    
            # Go to the next page number
            current_page += 1
            
        browser.close()
        
    
    print("Formatting data for Excel...")
    
    # Use a simple loop to add the Catalog Ranking (1, 2, 3...)
    for i in range(len(all_tvs)):
        all_tvs[i]['Catalog_Ranking'] = i + 1
        
    
    df = pd.DataFrame(all_tvs)
    
    
    column_order = ['Catalog_Ranking', 'Product_Name', 'Brand', 'Price', 'Rating', 'Description', 'Image_URL']
    df = df[column_order]
    
    
    df.to_excel('Croma_LED_TVs_Simple.xlsx', index=False)
    print("Done! Successfully saved", len(all_tvs), "TVs.")

if __name__ == "__main__":
    main()