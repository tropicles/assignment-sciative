from flask import Flask, render_template
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

NEON_URL = os.getenv("NEON_URL")

def get_db_connection():
    return psycopg2.connect(NEON_URL)

def get_tvs():
    # 1. Open the connection
    conn = get_db_connection()
    
    # 2. Use RealDictCursor so the data acts like a Python dictionary (perfect for HTML templates)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # 3. Write the raw SQL query to fetch all TVs 
    sql_query = "SELECT * FROM led_tv"
    
    # 4. Execute and fetch
    cursor.execute(sql_query)
    tv_list = cursor.fetchall()
    
    # 5. Always close your connections!
    cursor.close()
    conn.close()
    
    return tv_list

@app.route('/store')
def show_catalog():
   
    store_products = get_tvs()
    print(f"Found {len(store_products)} TVs in the database!")
    
    return render_template('index.html', products=store_products)
    
if __name__ == '__main__':
    app.run(debug=True)