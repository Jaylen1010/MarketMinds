from flask import Flask, render_template, request, session, redirect, jsonify
import yfinance as yf
import plotly.express as px
import plotly.io as pio
import plotly
import json
import main
import compare_
import ai
import news
from flask import Flask, session, abort, redirect, request
import google.auth
import google.auth.transport
import google.auth.transport.requests
import google.oauth2
import google.oauth2.id_token
from google_auth_oauthlib.flow import Flow
import os
import pathlib
import cachecontrol
import google
import requests
import functools
import user_backend
import datetime
import predictions

app = Flask(__name__)

app.secret_key = "jay"

responces = []
questions = []

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

client_secret_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

GOOGLE_CLIENT_ID = "130826755027-0fqceg698dr98j6c55au48vuhdldk2hs.apps.googleusercontent.com"

flow = Flow.from_client_secrets_file(client_secrets_file=client_secret_file,
                                     scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
                                    redirect_uri="http://127.0.0.1:5000/callback"
                                     )


def login_is_required(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return redirect('/')
        else:
            return function()
    
    return wrapper



@app.route("/")
def index():
    if "google_id" in session:
        return redirect("/home")
    else:
        return render_template("login.html")

@app.route("/login")
def login():
    auth_url, state = flow.authorization_url()

    session["state"] = state

    return redirect(auth_url)
 
@app.route("/callback")
def callback():

    try:
        flow.fetch_token(authorization_response=request.url)
        if not session['state'] == request.args['state']:
            abort(500)

        creds = flow.credentials
        request_session = requests.session()
        cahced_session = cachecontrol.CacheControl(request_session)
        token_request = google.auth.transport.requests.Request(session=cahced_session)

        id_info = google.oauth2.id_token.verify_oauth2_token(
            id_token=creds._id_token,
            request=token_request,
            audience=GOOGLE_CLIENT_ID
        )

        user_backend.add_user(id_info['given_name'], id_info['email'])

        session['google_id'] = id_info['sub']
        session['email'] = id_info['email']
        session['name'] = id_info['given_name'] + " " + id_info['family_name']

        return redirect('/home')
    except:
        return abort(504)


@app.route("/logout")
@login_is_required
def logout():
    session.clear()
    return redirect('/')

@app.route('/delete_account')
@login_is_required
def delete_account():
    user_backend.delete_user(session['email'])
    session.clear()

    return redirect('/')


@app.route('/historic')
@login_is_required
def historic():
    ticker = request.args.get('ticker')
    start = request.args.get('start')
    start = start.split(' ')[0]


    if ticker != "" and start != "max":
        user_backend.add_search_to_user(session['email'], {'name': ticker, 'start': start, 'end': datetime.datetime.now().strftime("%Y-%m-%d")})
        stock_data = yf.Ticker(ticker).history(start=start, end=datetime.datetime.now())
        stock = main.Stock(stock_data)
        long_name = stock.get_name(ticker)
        print("This one")
        return render_template("main.html",
                                                newsItems=news.get_stock_news(long_name),
                                                no_news=len(news.get_stock_news(long_name)) == 0,
                                                plot_html=main.get_fig(ticker, start, datetime.datetime.now().strftime("%Y-%m-%d")),
                                                current_price=stock.current_price(),
                                                mc=stock.get_market_cap(ticker),
                                                vol=stock.get_current_vol(),
                                                rsi_data=stock.plot_rsi(),
                                                dv=stock.garman_k_v()[1],
                                                av=stock.garman_k_v()[0],
                                                gkv=round(stock.garman_k_v()[2].tail(1)[0], 6),
                                                long_name=long_name)


    
    else:
        print(ticker, start)
        user_backend.add_search_to_user(session['email'], {'name': ticker, 'start': 'max', 'end': 'max'})
        stock = main.Stock(yf.Ticker(ticker).history("max"))
        long_name = stock.get_name(ticker)
        return render_template("main.html",
                                                newsItems=news.get_stock_news(long_name),
                                                no_news=len(news.get_stock_news(long_name)) == 0,
                                                plot_html=main.get_fig_max(ticker),
                                                current_price=stock.current_price(),
                                                mc=stock.get_market_cap(ticker),
                                                vol=stock.get_current_vol(),
                                                rsi_data=stock.plot_rsi(),
                                                dv=stock.garman_k_v()[1],
                                                av=stock.garman_k_v()[0],
                                                gkv=round(stock.garman_k_v()[2].tail(1)[0], 6),
                                                long_name=long_name)

@app.route('/whatif', methods=['GET', 'POST'])
def whatif():
    if request.method == 'POST':
        ticker = request.form['ticker1'].upper()
        try:
            amount = float(request.form['price'])
        except ValueError:
            return render_template('whatif.html', error="Invalid amount.")

        start_date = request.form['start_date']

        roi_data, error = main.whatif_roi(start_date, amount, ticker)
        if error:
            return render_template('whatif.html', error=error)
        return render_template('whatif.html', roi=roi_data)
    return render_template('whatif.html')

@app.route("/myportfolio", methods=['GET', 'POST'])
def portfolio():
    if request.method == "POST":
        ticker = request.form['ticker']
        amount = request.form['amount']
        date = request.form['date']
        user_backend.add_to_portfolio(session['email'], ticker, date, int(amount))

        portfolio_data = user_backend.get_portfolio_values(session['email'])
        return render_template('myportfolio.html', data=portfolio_data)
    else:
        portfolio_data = user_backend.get_portfolio_values(session['email'])
        return render_template('myportfolio.html', data=portfolio_data)

@app.route("/delete_port")
@login_is_required
def delete_port():
    deleteTicker = request.args.get('ticker')

    if deleteTicker:
        user_backend.remove_portfolio(session['email'], deleteTicker)

        return redirect('/myportfolio')

    else:
        return redirect('/myportfolio')


@app.route("/home", methods=["POST", "GET"])
@login_is_required
def home():
    ticker = request.args.get('ticker')
    

    if ticker:
        user_backend.add_search_to_user(session['email'], {'name': ticker, 'start': 'max', 'end': 'max'})
        stock = main.Stock(yf.Ticker(ticker).history("max"))
        long_name = stock.get_name(ticker)
        return render_template("main.html",
                                            newsItems=news.get_stock_news(long_name),
                                            no_news=len(news.get_stock_news(long_name)) == 0,
                                            plot_html=main.get_fig_max(ticker),
                                            current_price=stock.current_price(),
                                            mc=stock.get_market_cap(ticker),
                                            vol=stock.get_current_vol(),
                                            rsi_data=stock.plot_rsi(),
                                            dv=stock.garman_k_v()[1],
                                            av=stock.garman_k_v()[0],
                                            gkv=round(stock.garman_k_v()[2].tail(1)[0], 6),
                                            long_name=long_name)
    else:
        if request.method == "POST":
            ticker_name = request.form['company']

            start = request.form['start_date']
            end = request.form['end_date']


            try:

                stock = main.Stock(yf.Ticker(ticker_name).history(start=start, end=end))
            except:
                return render_template('main.html', error='Empty date or ticker name')


            long_name = stock.get_name(ticker_name)

            try:
                user_backend.add_search_to_user(session['email'], {'name': ticker_name, 'start': start, 'end':end})
                newsData = news.get_stock_news(long_name)
                no_news = len(newsData) == 0

                if ticker_name == "":
                    try:
                        print(long_name)
                        return render_template("main.html",
                                            newsItems=newsData,
                                            no_news=no_news,
                                            plot_html=main.get_fig(session['ticker_name'], start=start, end=end),
                                            current_price=stock.current_price(),
                                            mc=stock.get_market_cap(session['ticker_name']),
                                            vol=stock.get_current_vol(),
                                            rsi_data=stock.plot_rsi(),
                                            dv=stock.garman_k_v()[1],
                                            av=stock.garman_k_v()[0],
                                            gkv=round(stock.garman_k_v()[2].tail(1)[0], 6),
                                            long_name=long_name)
                    except:
                        return render_template("main.html", error="Ticker name or date invalid!")
                else:
                    try:
                        print(long_name)
                        session['ticker_name'] = ticker_name
                        return render_template("main.html",
                                            newsItems=newsData,
                                            no_news=no_news,
                                            plot_html=main.get_fig(ticker_name, start=start, end=end),
                                            current_price=stock.current_price(),
                                            mc=stock.get_market_cap(ticker_name),
                                            vol=stock.get_current_vol(),
                                            rsi_data=stock.plot_rsi(),
                                            dv=stock.garman_k_v()[1],
                                            av=stock.garman_k_v()[0],
                                            gkv=round(stock.garman_k_v()[2].tail(1)[0], 6),
                                            long_name=long_name)
                    except Exception as e:
                        print(e)
                        return render_template("main.html", error="Ticker name or date invalid!")
            except Exception as e:
                print(e)
                return render_template("main.html", error="Ticker name or date invalid! Whole")
        else:

            return render_template("main.html")

@app.route("/compare", methods=['POST', 'GET'])
@login_is_required
def compare():
    if request.method == "POST":
        ticker1 = request.form['ticker1']
        ticker2 = request.form['ticker2']

        start = request.form['start_date']
        end = request.form['end_date']


        try:

            fig_html = compare_.get_fig(ticker1, ticker2, start, end)
            fig_sec = compare_.get_sec_fig(ticker1, ticker2, start, end)

            return render_template('compare.html', plot_html=fig_html, sec_html=fig_sec)
        except:
            return render_template("compare.html", error='Ticker names or date invaild!')
    else:
        return render_template("compare.html")
    
@app.route("/ai", methods=["POST"])
@login_is_required
def chatbot():
    if request.method == "POST":
        question = request.form['question']
        questions.append(question)
        response = ai.anwser(question)
        responces.append(response)

        return jsonify({'response': response})


@app.route('/account')
@login_is_required
def account():
    email = session['email']
    search_history = user_backend.get_search_history_by_email(email)
    raw_tracked = user_backend.get_tracked_stocks_by_email(email)

    enriched_stocks = []

    for item in raw_tracked:
        # Determine if the entry is a dict (with added_at) or a plain ticker string
        if isinstance(item, dict):
            ticker = item.get('ticker')
            added_at = item.get('added_at')
        else:
            ticker = item
            added_at = "2025-06-10 13:00"  # Fallback if not available

        # Get price change info
        change_info = user_backend.get_price_change(ticker, added_at)
        
        stock_data = {"ticker": ticker}

        if isinstance(change_info, dict):
            stock_data.update(change_info)
        else:
            stock_data["change_error"] = change_info

        # Optionally include company name and current price if not already included
        name_price = user_backend.get_current_price(ticker)
        stock_data["name"] = name_price[0]
        stock_data["price"] = name_price[1]

        enriched_stocks.append(stock_data)


    return render_template(
        'account.html',
        username=session['name'],
        email=email,
        search_history=search_history,
        tracked_stocks=enriched_stocks,
    )

@app.route("/track", methods=['POST'])
@login_is_required
def track():
    if request.method == 'POST':
        tickerName = request.form['company']
        user_backend.add_tracked_stock_to_user(session['email'], tickerName)
        return redirect('/home')
    
    else:
        return redirect('/home')

@app.route("/delete")
@login_is_required
def delete():
    deleteTicker = request.args.get('ticker')

    if deleteTicker:
        user_backend.remove_tracked_stock(session['email'], deleteTicker)

        return redirect('/account')

    else:
        return redirect('/home')
    

@app.route('/clear')
@login_is_required
def clear():
    user_backend.clear_history(session['email'])
    return redirect('/account')


@app.route('/forecast/<ticker>')
def forecast_view(ticker):

    prediction = predictions.get_predict(ticker, 1000, 365)
    data = prediction[2]
    forecast = prediction[0]
    model = prediction[4]
    plots = predictions.generate_plot_html(data, forecast, ticker, model, prediction[5])
    

    return render_template("predictions.html", plots=plots, ticker=ticker)

@app.route("/predictroi", methods=['POST'])
def predictroi():

    ticker = request.args.get("ticker")
    range = request.args.get('days')
    amount = request.args.get('amount')
        

    return render_template('predict_roi.html', roi=predictions.get_predict(ticker, int(amount), int(range))[1], ticker=ticker, range=range, amount=amount)

    
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")

