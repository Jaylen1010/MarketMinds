import yfinance as yf
import plotly.express as px
import yfinance as yf
import plotly.express as px
import plotly.io as pio
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
import mpld3
import plotly.graph_objects as go
import plotly.subplots as subplt
from datetime import datetime
from dateutil.relativedelta import relativedelta 
import math
import pandas as pd

def date_difference(start_date_str, end_date_str, date_format="%Y-%m-%d"):
    # Convert to datetime objects
    start_date = datetime.strptime(start_date_str, date_format)
    end_date = datetime.strptime(end_date_str, date_format)

    # Get the calendar-based difference
    delta = relativedelta(end_date, start_date)

    # Get total number of days
    total_days = (end_date - start_date).days

    return f"{delta.years} years, {delta.months} months, {delta.days} days"

def get_fig_max(ticker):
    df = yf.Ticker(ticker).history("max")

    fig = go.Figure()

    # Add candlestick trace
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    ))

    # Add volume bar trace on secondary y-axis
    fig.add_trace(go.Bar(
        x=df.index,
        y=df['Volume'],
        name='Volume',
        marker_color='darkblue',
        yaxis='y2',
        opacity=0.3
    ))

    # Update layout
    fig.update_layout(
        title=f'{ticker} Stock Price - Max',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        xaxis_rangeslider_visible=True,
        template='ggplot2',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    plot_html_ = pio.to_html(fig, full_html=False)
    return plot_html_

def get_fig(ticker, start, end):
    df = yf.Ticker(ticker).history(start=start, end=end)

    fig = go.Figure()

    # Add candlestick trace
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    ))

    # Add volume bar trace on secondary y-axis
    fig.add_trace(go.Bar(
        x=df.index,
        y=df['Volume'],
        name='Volume',
        marker_color='darkblue',
        yaxis='y2',
        opacity=0.3
    ))

    # Update layout
    fig.update_layout(
        title=f'{ticker} Stock Price - {date_difference(start, end)}',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        xaxis_rangeslider_visible=True,
        template='ggplot2',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    plot_html_ = pio.to_html(fig, full_html=False)
    return plot_html_

class Stock:
    def __init__(self, data):
        self.df = data
    
    def get_name(self, ticker):
        stock = yf.Ticker(ticker)
        company_name = stock.info['longName']
        return company_name
      
    
    def current_price(self):
        current = self.df.tail(1)
        return "$" + str(round(current['Close'][0], 3))
    
    def get_market_cap(self, ticker):
        # Download the stock data using the ticker symbol
        stock = yf.Ticker(ticker)
        
        # Get the stock info (this contains a lot of financial information)
        stock_info = stock.info
        
        # Extract the market capitalization
        market_cap = stock_info.get('marketCap', 'Market Cap data not available')
        
        return "$" + str(market_cap) 
    
    def get_current_vol(self):
        current = self.df.tail(1)
        return str(current['Volume'][0]) + "M"
    
    def garman_k_v(self):
        gkv = ((np.log(self.df['High'])-np.log(self.df['Low']))**2)/2 - (2*np.log(2)-1)*((np.log(self.df['Close'])-np.log(self.df['Open']))**2)
    
        annualized_volatility = np.sqrt(gkv.mean() * 252) * 100


        daily_volatility = np.sqrt(gkv.mean()) * 100


        return  str(round(annualized_volatility, 4)) + "%",  str(round(daily_volatility, 4)) +  "%" , gkv
    


    def rsi(self, column='Close', window=14):
        close = self.df[column]
        
        delta = close.diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        

        rs = avg_gain / avg_loss
        

        rsi = 100 - (100 / (1 + rs))

        
        return rsi
    
    
    def plot_rsi(self, oversold=30, overbought=70):
        # Create a subplot with 2 rows, 1 column
        fig = subplt.make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,  # Share x-axis between subplots
            subplot_titles=('Stock Close Price', 'RSI (Relative Strength Index)'),
            vertical_spacing=0.1
        )

        # Plot stock Close price in the first subplot
        fig.add_trace(
            go.Scatter(x=self.df.index, y=self.df['Close'], mode='lines', name='Close Price'),
            row=1, col=1
        )

        # Plot RSI in the second subplot
        fig.add_trace(
            go.Scatter(x=self.df.index, y=self.rsi(), mode='lines', name='RSI', line=dict(color='orange')),
            row=2, col=1
        )

        # Add overbought and oversold lines in the RSI subplot
        fig.add_trace(
            go.Scatter(x=self.df.index, y=[overbought] * len(self.df), mode='lines', name=f'Overbought {overbought}', line=dict(color='red', dash='dash')),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(x=self.df.index, y=[oversold] * len(self.df), mode='lines', name=f'Oversold {oversold}', line=dict(color='green', dash='dash')),
            row=2, col=1
        )

        # Update layout to add titles, axis labels, and remove gaps between plots
        fig.update_layout(
            title_text="Stock Price and RSI Analysis",
            height=800,  # Height of the entire figure
            showlegend=True,
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            xaxis2_title="Date",
            yaxis2_title="RSI",
            margin=dict(l=40, r=40, t=40, b=40),  # Adjust margins
        )

        # Return the Plotly HTML string for embedding into a webpage
        html_plot = fig.to_html(full_html=False)

        return html_plot



def whatif_roi(date, amount, ticker):
    try:
        data = yf.Ticker(ticker).history(start=date, end=datetime.now().strftime("%Y-%m-%d"))
        if data.empty:
            return None, "No data available for this ticker and date."

        start_price = float(data['Close'].iloc[0])
        end_price = float(data['Close'].iloc[-1])

        percent_change = float(((end_price - start_price) / start_price) * 100)
        final_value = float(amount * (1 + percent_change / 100))
        investment_gain = float(final_value - amount)

        return {
            "start_price": round(start_price, 2),
            "end_price": round(end_price, 2),
            "percent_change": round(percent_change, 2),
            "investment_gain": round(investment_gain, 2),
            "final_value": round(final_value, 2),
            'ticker': ticker,
            'date': date,
            'invested': amount
        }, None
    except Exception as e:
        return None, str(e)



def predict_roi(amount, data):
    try:
        if data.empty:
            return None, "No data available for this ticker and date."

        today = datetime.now().date()
        data['ds'] = pd.to_datetime(data['ds'])

        # Get the latest prediction up to today
        current_data = data[data['ds'].dt.date <= today]

        if current_data.empty:
            return None, "No data available for today's date or earlier."

        # Get current and future values
        start_row = current_data.iloc[-1]
        end_row = data.iloc[-1]

        def calc_roi(start_price, end_price):
            percent_change = ((end_price - start_price) / start_price) * 100
            final_value = amount * (1 + percent_change / 100)
            gain = final_value - amount
            return {
                "start_price": round(start_price, 2),
                "end_price": round(end_price, 2),
                "percent_change": round(percent_change, 2),
                "investment_gain": round(gain, 2),
                "final_value": round(final_value, 2)
            }

        return {
            "yhat": calc_roi(start_row['yhat'], end_row['yhat']),
            "yhat_upper": calc_roi(start_row['yhat_upper'], end_row['yhat_upper']),
            "yhat_lower": calc_roi(start_row['yhat_lower'], end_row['yhat_lower']),
            "invested": amount
        }, None

    except Exception as e:
        return None, str(e)