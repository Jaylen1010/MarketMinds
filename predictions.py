import yfinance as yf
from prophet import Prophet
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import main
from prophet.plot import plot_components_plotly
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
from prophet.plot import plot_components_plotly
import pandas as pd

def change_data(ticker):
    data = yf.Ticker(ticker).history(period='10y')[['Close']].reset_index()

    data['Date'] = data['Date'].dt.tz_localize(None)

    data = data.rename(columns={"Date": "ds", "Close": "y"})

    return data


def get_predict_model(ticker, amount, range):
    data = change_data(ticker)

    model = Prophet()

    model.fit(data)

    future = model.make_future_dataframe(periods=range)
    forecast = model.predict(future)

    return forecast, main.predict_roi(amount, forecast)[0]['yhat'], data, ticker, model

def get_predict(ticker, amount, range):
    # Load and clean data
    data = change_data(ticker)
    
    # Feature engineering: Add holidays, changepoints, seasonality
    model = Prophet(
        daily_seasonality=True,
        yearly_seasonality=True,
        weekly_seasonality=True,
        changepoint_range=0.9,  # use more history for trend changes
        changepoint_prior_scale=0.5,  # control sensitivity to trend changes
        seasonality_mode='multiplicative'  # better for financial time series
    )

    # Add custom seasonalities (optional but helps with market cycles)
    model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    model.add_seasonality(name='quarterly', period=91.31, fourier_order=7)

    # Optionally add country-specific holidays
    from prophet.make_holidays import make_holidays_df
    try:
        from prophet.serialize import model_to_json
        model.add_country_holidays(country_name='US')  # or your market
    except Exception as e:
        print("Holidays not added:", e)

    # Fit the model
    model.fit(data)

    # Make future dataframe
    future = model.make_future_dataframe(periods=range)
    forecast = model.predict(future)

    # Optional: Evaluate model performance
    # df_cv = cross_validation(model, initial='180 days', period='30 days', horizon='60 days')
    # df_p = performance_metrics(df_cv)
    # print(df_p.head())

    # Return full forecast, predicted value, and model
    predicted_value = main.predict_roi(amount, forecast)[0]['yhat']
    return forecast, predicted_value, data, ticker, model, get_predict_model(ticker, amount, range)



def generate_plot_html(data, forecast, ticker, model, comp_model):
    

    html_outputs = {}

    # --- STYLE SETTINGS ---
    line_style_actual = dict(color='#1f77b4', width=2)
    line_style_predicted = dict(color='#2ca02c', width=2)
    line_style_bounds = dict(color='#ff7f0e', width=1, dash='dot')

    layout_style = dict(
        template='plotly_white',
        font=dict(family="Arial", size=14),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(l=40, r=30, t=50, b=40),
        width=1100,
        height=600
    )

    # --- ACTUAL vs PREDICTED ---
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=data['ds'], y=data['y'], mode='lines', name='Actual', line=line_style_actual))
    fig1.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Predicted', line=line_style_predicted))
    fig1.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_upper'], mode='lines', name='Upper Bound', line=line_style_bounds, opacity=0.6))
    fig1.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_lower'], mode='lines', name='Lower Bound', line=line_style_bounds, opacity=0.6))
    fig1.update_layout(title=f"<b>{ticker} Price Forecast vs Actual</b>", xaxis_title='Date', yaxis_title='Price ($)', **layout_style)
    html_outputs["actual_vs_predicted"] = pio.to_html(fig1, include_plotlyjs='cdn', full_html=False)

    # --- PROPHET COMPONENT PLOTS ---
    fig_components = plot_components_plotly(comp_model[4], comp_model[0])

    # Apply consistent styling and axis labels
    fig_components.update_layout(
        autosize=False,
        width=1100,
        height=900,
        template="plotly_white",
        font=dict(family="Arial", size=16),
        title=dict(
            text=f"<b>{ticker} Forecast: Trend & Seasonality Components</b>",
            x=0.5,
            xanchor='center',
            font=dict(size=22)
        ),
        margin=dict(l=40, r=30, t=60, b=40),
    )

    # Add axis labels manually
    fig_components.update_yaxes(title_text="Trend", row=1, col=1)
    fig_components.update_yaxes(title_text="Weekly Seasonality", row=2, col=1)
    fig_components.update_yaxes(title_text="Yearly Seasonality", row=3, col=1)

    fig_components.update_xaxes(title_text="Date", row=1, col=1)
    fig_components.update_xaxes(title_text="Day of Week", row=2, col=1)
    fig_components.update_xaxes(title_text="Day of Year", row=3, col=1)

    # Improve tooltips
    for trace in fig_components.data:
        trace.hovertemplate = "%{y:.2f}"

    html_outputs["prophet_components"] = pio.to_html(fig_components, include_plotlyjs=False, full_html=False)

    return html_outputs

