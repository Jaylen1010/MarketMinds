from google.cloud import firestore
import yfinance as yf
from datetime import datetime, timedelta
import main

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/jaylenhampton/Downloads/marketminds-9439b-febeb18deb95.json"
db = firestore.Client()
collection_ref = db.collection('users')

def add_user(name, email):
    # Check if user with the same email already exists
    existing_user = collection_ref.where('email', '==', email).limit(1).stream()
    if any(existing_user):
        print(f"User with email '{email}' already exists.")
        return

    # Add new user
    doc_ref = collection_ref.add({
        'name': name,
        'email': email,
        'searchs': [],
        'tracked_stocks': []
    })
    print("Document added with ID:", doc_ref[1].id)

def delete_user(email):
    docs = collection_ref.where('email', '==', email).stream()
    for doc in docs:
        doc.reference.delete()
        print(f"Deleted user with email: {email}")
        return
    print(f"No user found with email: {email}")

def get_all_users():
    users = collection_ref.stream()
    return [doc.to_dict() for doc in users]

def get_search_history_by_email(email):
    docs = collection_ref.where('email', '==', email).stream()
    for doc in docs:
        data = doc.to_dict()
        return data.get('searchs', [])
    

    return "theres none"

def get_current_price(tickerName):
    if isinstance(tickerName, list):
        tickerName = tickerName[0]  # just get the actual ticker string
    tk = yf.Ticker(tickerName)
    return tk.info['longName'], tk.info['currentPrice']

def get_tracked_stocks_by_email(email):
    docs = collection_ref.where('email', '==', email).stream()
    for doc in docs:
        data = doc.to_dict()
        return data.get('tracked_stocks', [])  # should return list of dicts
    return None

def add_search_to_user(email, search_entry):
    """
    search_entry example: {'name': 'tsla', 'start': '2024-09-10', 'end': '2025-09-10'}
    """
    docs = collection_ref.where('email', '==', email).stream()
    for doc in docs:
        doc.reference.update({
            'searchs': firestore.ArrayUnion([search_entry])
        })
        print(f"Added search to {email}")
        return
    print(f"No user found with email: {email}")

def add_tracked_stock_to_user(email, ticker_name):
    tracked_entry = {
        'ticker': ticker_name,
        'added_at': datetime.now().strftime("%Y-%m-%d %H:%M")
        
    }

    docs = collection_ref.where('email', '==', email).stream()
    for doc in docs:
        doc.reference.update({
            'tracked_stocks': firestore.ArrayUnion([tracked_entry])
        })
        print(f"Added tracked stock to {email}")
        return
    print(f"No user found with email: {email}")

def add_to_portfolio(email, ticker_name, date, amount):
    tracked_entry = {
        'ticker': ticker_name,
        'date': date,
        'invested': amount,
        'date_added': datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    docs = collection_ref.where('email', '==', email).stream()

    for doc in docs:
        doc.reference.update({
            'portfolio': firestore.ArrayUnion([tracked_entry])
        })
        print(f'Added stock to {email} portfolio')
    
    print(f' No user found with {email}')

def get_portfolio(email):
    docs = collection_ref.where('email', '==', email).stream()
    for doc in docs:
        data = doc.to_dict()
        return data.get('portfolio', [])  # should return list of dicts
    return None


def remove_portfolio(email, ticker_name):
    docs = collection_ref.where('email', '==', email).stream()
    for doc in docs:
        data = doc.to_dict()
        current_list = data.get('portfolio', [])

        # Find the exact entry with the matching ticker
        to_remove = next((entry for entry in current_list if entry.get('ticker') == ticker_name), None)
        if to_remove:
            doc.reference.update({
                'portfolio': firestore.ArrayRemove([to_remove])
            })
            print(f"Removed tracked stock '{ticker_name}' from {email}")
        else:
            print(f"Ticker '{ticker_name}' not found for {email}")
        return
    print(f"No user found with email: {email}")


def remove_tracked_stock(email, ticker_name):
    docs = collection_ref.where('email', '==', email).stream()
    for doc in docs:
        data = doc.to_dict()
        current_list = data.get('tracked_stocks', [])

        # Find the exact entry with the matching ticker
        to_remove = next((entry for entry in current_list if entry.get('ticker') == ticker_name), None)
        if to_remove:
            doc.reference.update({
                'tracked_stocks': firestore.ArrayRemove([to_remove])
            })
            print(f"Removed tracked stock '{ticker_name}' from {email}")
        else:
            print(f"Ticker '{ticker_name}' not found for {email}")
        return
    print(f"No user found with email: {email}")


def clear_history(email):
    docs = collection_ref.where('email', '==', email).stream()
    for doc in docs:
        doc.reference.update({
            'searchs': []
        })
        print(f"Cleared search history for {email}")
        return
    print(f"No user found with email: {email}")


def get_tracked(email):
    stocks = []
    for stock in get_tracked_stocks_by_email(email):
        ticker = stock['ticker']
        added_at = stock.get('added_at', 'N/A')
        name, price = get_current_price(ticker)
        
        stocks.append({
            'ticker': ticker,
            'name': name,
            'price': price,
            'added_at': added_at
        })

    return stocks


def get_price_change(ticker, previous_datetime_str):
    previous_datetime = datetime.strptime(previous_datetime_str, "%Y-%m-%d %H:%M")
    now = datetime.now()

    # Use '1d' interval for anything older than a day OR after market hours
    market_close_hour = 16  # 4 PM
    use_daily = now.hour >= market_close_hour or (now - previous_datetime).days >= 1

    interval = "1d" if use_daily else "1m"

    stock = yf.Ticker(ticker)
    
    # Cap `end` to today for '1d' since yfinance won't return future timestamps
    if interval == "1d":
        end_time = (now + timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        end_time = (now + timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M')

    hist = stock.history(start=previous_datetime.strftime('%Y-%m-%d'), end=end_time, interval=interval)

    if hist.empty:
        return {"change_error": f"No data for {ticker} between {previous_datetime_str} and now."}

    try:
        prev_price = hist.iloc[0]['Close']
    except Exception:
        return {"change_error": f"Couldn't determine previous price for {ticker}."}

    current_price = hist['Close'].iloc[-1]

    price_change = current_price - prev_price
    percent_change = (price_change / prev_price) * 100

    return {
        "previous_price": round(prev_price, 2),
        "current_price": round(current_price, 2),
        "price_change": round(price_change, 2),
        "percent_change": round(percent_change, 2),
        "previous_datetime": previous_datetime.strftime("%Y-%m-%d %H:%M")
    }



def get_portfolio_values(email):
    try:
        portfolio = get_portfolio(email)
        port_values = []
        total_price = 0
        total_price_change = 0

        for port in portfolio:
            total_price += port['invested']
            value = main.whatif_roi(port['date'], port['invested'], port['ticker'])
            # assuming whatif_roi returns a list of dicts like [{'ticker': 'AAPL', 'investment_gain': 53, 'percent_change': 5.3, 'date': '2024-04-01', 'invested': 1000}]
            port_values.append(value[0])

        for value in port_values:
            total_price_change += value['investment_gain']

        percent_change = float((total_price_change / total_price) * 100) if total_price > 0 else 0

        return {
            'total_price': total_price,
            'port_values': port_values,
            'total_price_change': round(total_price_change, 3),
            'percent_change': round(percent_change, 3),
            'total_amount': round((total_price + total_price_change), 3),
        }
    except Exception as e:
        print(f"Error: {e}")
        return None


