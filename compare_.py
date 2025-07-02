import yfinance as yf
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import main

def get_fig(ticker1, ticker2, start, end):
    df1 = yf.Ticker(ticker1).history(start=start, end=end)
    df2 = yf.Ticker(ticker2).history(start=start, end=end)

    # Create subplot grid with shared X-axis
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f"{ticker1} Candlestick", f"{ticker2} Candlestick"),
        row_heights=[0.5, 0.5]
    )

    # Add candlestick for first ticker
    fig.add_trace(go.Candlestick(
        x=df1.index,
        open=df1['Open'],
        high=df1['High'],
        low=df1['Low'],
        close=df1['Close'],
        name=ticker1
    ), row=1, col=1)

    # Add candlestick for second ticker
    fig.add_trace(go.Candlestick(
        x=df2.index,
        open=df2['Open'],
        high=df2['High'],
        low=df2['Low'],
        close=df2['Close'],
        name=ticker2
    ), row=2, col=1)

    fig.update_layout(
        title=f"Candlestick Comparison: {ticker1} vs {ticker2} ({main.date_difference(start, end)})",
        template='plotly_white',
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=True,
        height=800,
        showlegend=False
    )

    plot_html_ = pio.to_html(fig, full_html=False)
    return plot_html_


def get_sec_fig(ticker1, ticker2, start, end, type="Close"):
    # Fetch historical data for both tickers
    df1 = yf.Ticker(ticker1).history(start=start, end=end)
    df2 = yf.Ticker(ticker2).history(start=start, end=end)

    df1['MA20'] = df1[type].rolling(window=20).mean()
    df2['MA20'] = df2[type].rolling(window=20).mean()

    fig = go.Figure()

    # Add first ticker line
    fig.add_trace(go.Scatter(
        x=df1.index,
        y=df1[type],
        mode='lines+markers',
        name=f"{ticker1} {type}",
        line=dict(width=2, color='blue'),
        marker=dict(size=4),
        hovertemplate=f"%{{x|%b %d, %Y}}<br>{ticker1} {type}: %{{y:.2f}}<extra></extra>"
    ))

    # Add second ticker line
    fig.add_trace(go.Scatter(
        x=df2.index,
        y=df2[type],
        mode='lines+markers',
        name=f"{ticker2} {type}",
        line=dict(width=2, color='green'),
        marker=dict(size=4),
        hovertemplate=f"%{{x|%b %d, %Y}}<br>{ticker2} {type}: %{{y:.2f}}<extra></extra>"
    ))


   

    # Update layout
    fig.update_layout(
        title=f"{type} Prices: {ticker1} vs {ticker2} ({main.date_difference(start, end)})",
        xaxis_title="Date",
        yaxis_title=f"{type} Price (USD)",
        legend_title="Ticker",
        hovermode='x unified',
        template='plotly_white',
        
        yaxis=dict(showgrid=True),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    plot_html_ = pio.to_html(fig, full_html=False)
    return plot_html_
