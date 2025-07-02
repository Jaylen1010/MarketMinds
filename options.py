import predictions

def extract_predicted_prices(forecast, days_ahead):
    return forecast[['ds', 'yhat']].tail(days_ahead).reset_index(drop=True)


def best_call_trade_from_forecast(predicted_prices, strike_price, premium):
    best_profit = 0
    best_buy_day = None
    best_sell_day = None
    buy_day_vaule = None
    sell_day_vaule = None
    profit = None
    intrinsic_value = None

    for i in range(len(predicted_prices)):
        for j in range(i + 1, len(predicted_prices)):
            buy_day = predicted_prices.loc[i]
            sell_day = predicted_prices.loc[j]

            intrinsic_value = max(0, sell_day['yhat'] - strike_price)
            profit = intrinsic_value - premium

            if profit > best_profit:
                best_profit = profit
                best_buy_day = buy_day['ds']
                buy_day_vaule = buy_day['yhat']
                best_sell_day = sell_day['ds']
                sell_day_vaule = sell_day['yhat']

    return {
        'best_profit': best_profit,
        'buy_date': f'{best_buy_day} at {buy_day_vaule}$',
        'sell_date': f'{best_sell_day} at {sell_day_vaule}',
        'profit': profit,
        'iv': intrinsic_value
    }


forecast, predicted_value, data, ticker, model, _ = predictions.get_predict('TSLA', 1000, 365)
predicted_prices = extract_predicted_prices(forecast, 365)


today_price = data['y'].iloc[-1]
strike_price = round(today_price + 1) # todays price
premium = 200

trade = best_call_trade_from_forecast(predicted_prices, strike_price, premium)

print(f"Buy option on {trade['buy_date']}")
print(f"Sell option on {trade['sell_date']}")
print(f"Expected profit: ${trade['best_profit']:.2f}")
print(f'IV: {trade['iv']}')