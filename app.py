from flask import Flask, render_template, request
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv
import math

app = Flask(__name__)
load_dotenv()

NEON_URL = os.getenv("NEON_URL")

def get_db_connection():
    return psycopg2.connect(NEON_URL)

def get_tvs(search_query="", sort_by="ranking", page=1, per_page=12):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # 1. Sort Logic
    sort_options = {
        "price_low": "ORDER BY price ASC",
        "ranking": "ORDER BY catalog_ranking ASC",
        "top_rated": "ORDER BY rating DESC"
    }
    order_clause = sort_options.get(sort_by, "ORDER BY catalog_ranking ASC")
    
    # Pagination Math
    offset = (page - 1) * per_page
    
    where_clause = ""
    params = []
    
    # 2. Search Logic
    if search_query:
        where_clause = "WHERE product_name ILIKE %s OR brand ILIKE %s"
        search_pattern = f"%{search_query}%"
        params = [search_pattern, search_pattern]
        
    # 3. Get TOTAL count of matching TVs (so we know how many pages to make)
    count_query = f"SELECT COUNT(*) as total FROM led_tv {where_clause};"
    cursor.execute(count_query, tuple(params))
    total_items = cursor.fetchone()['total']
    
    # 4. Get the ACTUAL data for just this page
    data_query = f"""
        SELECT * FROM led_tv 
        {where_clause} 
        {order_clause} 
        LIMIT %s OFFSET %s;
    """
    # Combine the search parameters with the pagination numbers
    data_params = params + [per_page, offset]
    cursor.execute(data_query, tuple(data_params))
    
    tv_list = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Calculate how many pages there are in total
    total_pages = math.ceil(total_items / per_page)
    
    return tv_list, total_pages

@app.route('/store')
def show_catalog():
    current_search = request.args.get('q', '')
    current_sort = request.args.get('sort', 'ranking')
    
    # Safely get the page number from the URL, default to 1
    try:
        current_page = int(request.args.get('page', 1))
        if current_page < 1:
            current_page = 1
    except ValueError:
        current_page = 1
        
    # Pass everything to our new function
    store_products, total_pages = get_tvs(current_search, current_sort, current_page)
    
    return render_template('index.html', 
                           products=store_products, 
                           search_query=current_search,
                           current_sort=current_sort,
                           current_page=current_page,
                           total_pages=total_pages)

if __name__ == '__main__':
    app.run(debug=True)