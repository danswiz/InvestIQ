from flask import Flask, render_template, jsonify
import os
import json
import traceback
import sys

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "ok", "python": sys.version})

@app.route('/debug')
def debug():
    info = {
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "files": os.listdir('.'),
        "imports": {}
    }
    
    try:
        import numpy
        info["imports"]["numpy"] = str(numpy.__version__)
    except Exception as e:
        info["imports"]["numpy"] = f"FAILED: {str(e)}"
    
    try:
        import pandas
        info["imports"]["pandas"] = str(pandas.__version__)
    except Exception as e:
        info["imports"]["pandas"] = f"FAILED: {str(e)}"
    
    try:
        import yfinance
        info["imports"]["yfinance"] = str(yfinance.__version__)
    except Exception as e:
        info["imports"]["yfinance"] = f"FAILED: {str(e)}"
    
    try:
        from dataclasses import dataclass, asdict
        info["imports"]["dataclasses"] = "OK"
    except Exception as e:
        info["imports"]["dataclasses"] = f"FAILED: {str(e)}"
    
    try:
        from rater import BreakoutRater
        info["imports"]["rater"] = "OK"
    except Exception as e:
        info["imports"]["rater"] = f"FAILED: {str(e)}"
    
    return jsonify(info)

@app.route('/')
def index():
    data = {"last_scan": "Awaiting scan", "stocks": []}
    if os.path.exists('top_stocks.json'):
        try:
            with open('top_stocks.json', 'r') as f:
                data = json.load(f)
        except:
            pass
    return render_template('index.html', stocks=data.get('stocks', []), last_scan=data.get('last_scan'))

@app.route('/api/rate/<ticker>')
def rate_ticker(ticker):
    """Read from cached top_stocks.json for consistency with list view"""
    try:
        ticker = ticker.upper()
        if os.path.exists('top_stocks.json'):
            with open('top_stocks.json', 'r') as f:
                data = json.load(f)
                stocks = data.get('stocks', [])
                for stock in stocks:
                    if stock['ticker'] == ticker:
                        # Fetch live news only
                        try:
                            import yfinance as yf
                            stock_obj = yf.Ticker(ticker)
                            news_items = []
                            raw_news = stock_obj.news or []
                            for n in raw_news[:5]:
                                content = n.get('content', {})
                                title = content.get('title')
                                publisher = content.get('provider', {}).get('displayName')
                                link = content.get('canonicalUrl', {}).get('url')
                                pub_date = content.get('pubDate')
                                if title:
                                    time_str = "Recently"
                                    if pub_date:
                                        try:
                                            from datetime import datetime
                                            dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                                            time_str = dt.strftime('%b %d, %H:%M')
                                        except:
                                            time_str = pub_date[:16] if pub_date else "Recently"
                                    news_items.append({
                                        "title": title,
                                        "publisher": publisher or "Yahoo Finance",
                                        "link": link,
                                        "time": time_str
                                    })
                        except:
                            news_items = []
                        
                        # Return cached rating + live news
                        return jsonify({
                            "ticker": stock['ticker'],
                            "name": stock['name'],
                            "sector": stock['sector'],
                            "industry": stock.get('industry', 'N/A'),
                            "score": stock['score'],
                            "grade": stock['grade'],
                            "max_score": 100,
                            "technical_score": stock.get('technical_score', 0),
                            "growth_score": stock.get('growth_score', 0),
                            "quality_score": stock.get('quality_score', 0),
                            "context_score": stock.get('context_score', 0),
                            "market_cap": stock.get('market_cap', 0),
                            "results": [],
                            "news": news_items,
                            "valuation": {
                                "forward_pe": None,
                                "trailing_pe": None,
                                "peg_ratio": None,
                                "book_value": None,
                                "price_to_book": None,
                                "roe": None
                            },
                            "opinions": {
                                "recommendation": "N/A",
                                "target_mean": None,
                                "analysts": 0
                            }
                        })
        return jsonify({"error": f"{ticker} not found in cache"}), 404
    except Exception as e:
        return jsonify({"error": f"Error reading cache: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18791, debug=True)
