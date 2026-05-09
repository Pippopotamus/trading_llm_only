import requests
import pandas as pd
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta


def fn_json_to_pandas(json):
    json_file = json.json()
    price_json = json_file['candles']
    times = []
    granularity = []
    close_price, high_price, low_price, open_price = [], [], [], []

    for candle in price_json:
        dt_time = pd.to_datetime(
            datetime.fromisoformat(
                candle['time'][:-1] + '+00:00')
            .astimezone(ZoneInfo('US/Eastern')))
        times.append(dt_time)
        granularity.append(json_file['granularity'])
        close_price.append(float(candle['mid']['c']))
        high_price.append(float(candle['mid']['h']))
        low_price.append(float(candle['mid']['l']))
        open_price.append(float(candle['mid']['o']))

    df = pd.DataFrame({'datetime': pd.to_datetime(times).tz_localize(None),
                       'interval': granularity,
                       'close': close_price,
                       'high': high_price,
                       'low': low_price,
                       'open': open_price})
    df.index = pd.to_datetime(times).tz_localize(None)
    return df


def fn_oanda_historical(currency,
                        oanda_token,
                        oanda_url,
                        oanda_acct
                        ):
    li_interval = ['M5', 'M15', 'M30', 'H1', 'H4', 'D']
    li_lookback = [15, 30, 30, 30, 60, 90]
    df = pd.DataFrame()

    for interval, lookback in zip(li_interval, li_lookback):
        # Get historical prices
        start_time = datetime.now() - relativedelta(days=lookback)
        start_time = time.mktime(start_time.timetuple())
        end_time = time.mktime(datetime.now().timetuple()) - 1

        headers = {'Authorization': 'Bearer ' + oanda_token}
        query = {
            'from': str(start_time),
            'to': str(end_time),
            'granularity': interval,
        }

        candles_path = f'/v3/accounts/{oanda_acct}/instruments/{currency}/candles'
        response = requests.get('https://' + oanda_url + candles_path,
                                headers=headers,
                                params=query)
        print(f'Historical Prices Response (Interval: {interval}): {response.status_code}')

        if response.status_code != 200:
            print('ERROR: ' + response.text)

        df_temp = fn_json_to_pandas(response)
        df = pd.concat([df, df_temp], ignore_index=True)
    return df


def fn_oanda_current(currency,
                     oanda_token,
                     oanda_url,
                     oanda_acct
                     ):
    headers = {'Authorization': 'Bearer ' + oanda_token}
    pricing_path = f'/v3/accounts/{oanda_acct}/pricing?instruments={currency}'
    response = requests.get('https://' + oanda_url + pricing_path,
                            headers=headers
                            )
    print(f'Current Pricing Response: {response.status_code}')

    cba_time = pd.to_datetime(
        datetime.fromisoformat(
            response.json()['time'][:-1] + '+00:00')
        .astimezone(ZoneInfo('US/Eastern'))).tz_localize(None)
    bid = float(response.json()["prices"][0]['bids'][0]['price'])
    ask = float(response.json()["prices"][0]['asks'][0]['price'])
    spread = round(abs(bid - ask), 5)

    df = pd.DataFrame([{
        'currency': currency,
        'time': cba_time,
        'bid': bid,
        'ask': ask,
        'spread': spread
    }])
    return df
