import sqlite3
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def generate_top_stocks_json():
    print("Generating top_stocks.json for Vercel...")
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    # Get top 50 stocks by score
    stocks = conn.execute('SELECT * FROM tickers ORDER BY score DESC LIMIT 50').fetchall()
    
    data = []
    for s in stocks:
        data.append(dict(s))
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_dir, 'data', 'top_stocks.json')
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    conn.close()
    print(f"✅ Generated top_stocks.json with {len(data)} stocks.")

if __name__ == "__main__":
    generate_top_stocks_json()
