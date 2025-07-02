import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor

def add_technical_indicators(df):
    df['SMA_5'] = df['Close'].rolling(5).mean()
    df['SMA_10'] = df['Close'].rolling(10).mean()
    df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
    df['Momentum'] = df['Close'] - df['Close'].shift(5)
    df['Volatility'] = df['Close'].rolling(10).std()
    df['Return_1d'] = df['Close'].pct_change()

    for lag in range(1, 6):
        df[f'Return_lag_{lag}'] = df['Return_1d'].shift(lag)
    df.dropna(inplace=True)
    return df

def train_model(df, features):
    df['Target'] = df['Return_1d'].shift(-1)
    df.dropna(inplace=True)

    X = df[features]
    y = df['Target']

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

def safe_float(val):
    # Convert val to float scalar if possible
    if isinstance(val, (list, np.ndarray, pd.Series)):
        if len(val) == 1:
            return float(val[0])
        else:
            # If multiple elements, take last
            return float(val[-1])
    return float(val)

def iterative_forecast(model, last_known_data, days, features):
    preds = []
    data = last_known_data.copy()

    for day in range(days):
        X_feat = pd.DataFrame([{feat: safe_float(data[feat]) for feat in features}])
        pred_return = model.predict(X_feat)[0]
        preds.append(pred_return)

        # Shift lag returns down by one day
        for lag in reversed(range(2, 6)):
            data[f'Return_lag_{lag}'] = data[f'Return_lag_{lag -1}']
        data['Return_lag_1'] = pred_return

    return preds


def main():
    ticker = input("Enter ticker (e.g., AAPL): ").strip().upper()
    days_to_forecast = int(input("How many days ahead to forecast? "))
    print(f"Downloading {ticker} data...")
    df = yf.Ticker(ticker).history("max")


    df = add_technical_indicators(df)

    features = ['SMA_5', 'SMA_10', 'EMA_10', 'Momentum', 'Volatility'] + [f'Return_lag_{i}' for i in range(1,6)]

    model = train_model(df, features)

    last_row = df.iloc[-1]
    # Build last_known_data dict of floats only
    last_known_data = {feat: safe_float(last_row[feat]) for feat in features}

    preds = iterative_forecast(model, last_known_data, days_to_forecast, features)

    # Convert predicted returns to prices
    last_price = df['Close'].iloc[-1]
    predicted_prices = [last_price * (1 + preds[0])]
    for r in preds[1:]:
        predicted_prices.append(predicted_prices[-1] * (1 + r))

    # Plot recent actual prices + forecast
    plt.figure(figsize=(12,6))
    plt.plot(df.index[-60:], df['Close'].tail(60), label="Recent Actual Prices")
    future_dates = pd.bdate_range(df.index[-1], periods=days_to_forecast + 1)[1:]
    plt.plot(future_dates, predicted_prices, label=f"Forecast Next {days_to_forecast} Days")
    plt.title(f"{ticker} Price Forecast with Random Forest")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    main()
