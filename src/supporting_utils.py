import yfinance as yf
import pandas as pd
import oanda_pricing
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

# FTSE for GBP Pairs
def fn_ftse():
    # Define the ticker symbol for the FTSE 100
    print('Getting FTSE 100')
    ticker_symbol = "^FTSE"

    # Get data for the ticker
    df_ftse = yf.download(ticker_symbol,
                          start=(datetime.now() - relativedelta(days=60)).strftime('%Y-%m-%d'),
                          end=datetime.now().strftime('%Y-%m-%d'),
                          auto_adjust=True)

    df_ftse.columns = df_ftse.columns.droplevel(1)
    df_ftse.reset_index(drop=False, inplace=True)
    df_ftse = df_ftse.round(2)

    return df_ftse

# Dollar Index (dxy)
def fn_dxy(oanda):
    df = pd.DataFrame()
    li_dxy_currencies = ['EUR_USD', 'USD_JPY', 'GBP_USD', 'USD_CAD', 'USD_SEK', 'USD_CHF']

    for currency in li_dxy_currencies:
        print('DXY Currency: ' + currency)
        df_temp = oanda.fn_oanda_dxy(currency)
        df_temp['currency'] = currency
        df = pd.concat([df, df_temp], ignore_index=True)

    li_ohlc = ['open', 'high', 'low', 'close']

    df_pvt = df.pivot(index=['datetime', 'interval'],
                      columns='currency',
                      values=li_ohlc)

    for ohlc in li_ohlc:
        df_pvt[('dxy',ohlc)] = 50.14348112 * \
            (df_pvt[(ohlc,'EUR_USD')] ** -0.576) * \
            (df_pvt[(ohlc,'USD_JPY')] ** 0.136) * \
            (df_pvt[(ohlc,'GBP_USD')] ** -0.119) * \
            (df_pvt[(ohlc,'USD_CAD')] ** 0.091) * \
            (df_pvt[(ohlc,'USD_SEK')] ** 0.042) * \
            (df_pvt[(ohlc,'USD_CHF')] ** 0.036)

    df_pvt.drop(li_ohlc, axis=1, inplace=True)
    df_pvt.reset_index(inplace=True)

    df_pvt.columns = df_pvt.columns.get_level_values(1)
    df_pvt.columns.name = 'dxy'
    df_pvt.columns = ['datetime', 'interval', 'open', 'high', 'low', 'close']
    df_pvt.sort_values(['interval', 'datetime'], inplace=True)

    return df_pvt