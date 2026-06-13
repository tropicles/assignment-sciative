from flask import Flask, render_template, request
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

NEON_URL = os.getenv("NEON_URL")

def get_db_connection():
    return psycopg2.connect(NEON_URL)

def get_tvs(search_query=""):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # 1. If the user searched for something
    if search_query:
        
        sql_query = """
            SELECT * FROM led_tv 
            WHERE product_name ILIKE %s OR brand ILIKE %s;
        """
        search_pattern = f"%{search_query}%"
        cursor.execute(sql_query, (search_pattern, search_pattern))
    
    # 2. If there is NO search query (Default Page Load)
    else:
        
        sql_query = "SELECT * FROM led_tv ORDER BY RANDOM();"
        cursor.execute(sql_query)
        
    tv_list = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return tv_list

@app.route('/store')
def show_catalog():
    current_search = request.args.get('q', '')
    
    store_products = get_tvs(current_search)
    
    return render_template('index.html', products=store_products, search_query=current_search)

if __name__ == '__main__':
    app.run(debug=True)