import ast
import requests
import pandas as pd
import time
import numpy as np
from datetime import datetime

def fn_extract_trading_array(response_llm):
    trading_array_str = (response_llm[response_llm.find('TRADING_ARRAY'):]
                         .replace('TRADING_ARRAY:', ''))
    trading_array_num = ast.literal_eval(trading_array_str[trading_array_str.find('['):trading_array_str.find(']') + 1])

    return trading_array_num


def fn_extract_stay_exit(response_llm):
    response_llm.find('STAY_EXIT')
    stay_exit_str = (response_llm[response_llm.find('STAY_EXIT'):]
                         .replace('STAY_EXIT:', ''))
    stay_exit_num = ast.literal_eval(stay_exit_str[stay_exit_str.find('['):stay_exit_str.find(']') + 1])
    return stay_exit_num


def fn_lot_size(oanda_token,
                oanda_url,
                oanda_acct,
                risk,
                llm_response):

    headers = {'Authorization': 'Bearer ' + oanda_token}

    acct_path = '/v3/accounts/' + oanda_acct
    response = requests.get('https://' + oanda_url + acct_path, headers=headers)
    print(f'Account Balance Status Code: {response.status_code}')
    balance = response.json()['account']['balance']

    trading_array = fn_extract_trading_array(llm_response)
    entry = trading_array[0]
    stop_loss = trading_array[1]

    risk_amt = round(float(balance) / round(abs(entry - stop_loss), 5) * risk, 5)
    return risk_amt


def fn_place_trade(currency,
                   response_llm,
                   risk,
                   end_hour,
                   oanda_token,
                   oanda_url,
                   oanda_acct
                   ):

    trading_array = fn_extract_trading_array(response_llm)

    entry = trading_array[0]
    stop_loss = trading_array[1]
    take_profit = trading_array[2]
    trailing_stop = round(abs(stop_loss - entry), 5)

    if trading_array == [0, 0, 0]:
        print('No trades were recommended.')
        df = pd.DataFrame([{
            'currency': currency,
            'buy_sell': None,
            'trade_id': None,
            'order': None,
            'order_response': None,
            'stop_loss': None,
            'stop_loss_response': None,
            'take_profit': None,
            'take_profit_response': None,
            'error': 'no trade'
        }])
        return df

    print(f'Entry Price: {entry}')
    print(f'Stop Loss: {stop_loss}')
    print(f'Take Profit: {take_profit}')

    if take_profit > entry:
        buy_sell = 'Buy'
        trend_sign = 1
    elif take_profit < entry:
        buy_sell = 'Sell'
        trend_sign = -1
    else:
        print('ERROR')
        df = pd.DataFrame([{
            'currency': currency,
            'buy_sell': None,
            'trade_id': None,
            'order': None,
            'order_response': None,
            'stop_loss': None,
            'stop_loss_response': None,
            'take_profit': None,
            'take_profit_response': None,
            'error': 'error'
        }])
        return df

    # Calculate Lot Size
    lot_size = fn_lot_size(oanda_token=oanda_token,
                           oanda_url=oanda_url,
                           oanda_acct=oanda_acct,
                           risk=risk,
                           llm_response=response_llm
                           )

    # Place Order
    print(f'Placing {buy_sell} trade for {currency}')
    units = int(trend_sign*lot_size)
    now = datetime.now()
    good_til_date = datetime(now.year, now.month, now.day, end_hour, 59, 59)
    # good_til_date = time.mktime(datetime.now().timetuple()) + 3600*24
    headers = {'Authorization': 'Bearer ' + oanda_token}
    orders_path = f'/v3/accounts/{oanda_acct}/orders'
    order = {'order': {
        'units': f'{units}',
        'instrument': f'{currency}',
        'price': f'{entry}',
        'timeInForce': 'GTD',
        'gtdTime': str(good_til_date),
        'type': 'MARKET_IF_TOUCHED',       # MARKET   LIMIT MARKET_IF_TOUCHED
        'positionFill': 'DEFAULT',
        'stopLossOnFill': {
            'timeInForce': 'GTC',
            'price': f'{stop_loss}'
        },
        'takeProfitOnFill': {
            'price': f'{take_profit}'
        },
        'trailingStopLossOnFill ': {
            'timeInForce': 'GTC',
            'distance': f'{trailing_stop}'
        }
    }}

    response_order = requests.post('https://' + oanda_url + orders_path, headers=headers, json=order)
    print(f'Order Response: {response_order.status_code}')
    if response_order.status_code != 201:
        print(response_order.text)

    trade_id = response_order.json()['orderCreateTransaction']['id']
    print(f'Order Number: {trade_id}')

    df = pd.DataFrame([{
        'currency': currency,
        'buy_sell': buy_sell,
        'trade_id': trade_id,
        'order': order,
        'order_response': f'{response_order.status_code}',
        'error': None
    }])
    return df


def fn_modify_trade(oanda_token,
                    oanda_url,
                    oanda_acct,
                    currency,
                    trade_id,
                    response_llm
                    ):

    stay_exit = fn_extract_trading_array(response_llm)

    if stay_exit == 'stay':
        print(f'Stay in trade for {currency}')
        return None
    elif stay_exit == 'exit':
        headers = {'Authorization': 'Bearer ' + oanda_token}
        orders_path = f'/v3/accounts/{oanda_acct}/orders'
        order = {
            'trade_id': trade_id,
        }
        response_order = requests.post('https://' + oanda_url + orders_path, headers=headers, json=order)
        print(f'Order Response: {response_order.status_code}')
        print(f'Trade Closed for {currency}')

        # Find the response, find the request json format
        if response_order.status_code != 201:
            print(response_order.text)

        return response_order
    else:
        print('ERROR! With stay_exit')
        return None


def fn_open_orders(oanda_token,
                   oanda_url,
                   oanda_acct
                   ):
    # Orders
    headers = {'Authorization': 'Bearer ' + oanda_token}
    pricing_path = f'/v3/accounts/{oanda_acct}/orders'
    response = requests.get('https://' + oanda_url + pricing_path,
                            headers=headers
                            )
    print(f'Open Orders Response: {response.status_code}')

    if response.json()['orders'] == []:
        df_orders = None
    else:
        df_orders = pd.DataFrame(response.json()['orders'])
        df_orders = df_orders[df_orders['type'] == 'MARKET_IF_TOUCHED']

        if not df_orders.empty:
            try:
                df_orders['stopLoss'] = df_orders['stopLossOnFill'].apply(lambda x: x['price'] if x != '' else None)
            except KeyError:
                df_orders['stopLoss'] = None
            try:
                df_orders['trailingStopLoss'] = round(abs(df_orders['price'] - df_orders['trailingStopLossOnFill']), 5)
            except KeyError:
                df_orders['trailingStopLoss'] = None
            try:
                df_orders['takeProfit'] = df_orders['takeProfitOnFill'].apply(lambda x: x['price'] if x != '' else None)
            except KeyError:
                df_orders['takeProfit'] = None

            df_orders['gtdTime'] = (pd.to_datetime(df_orders['gtdTime'])
                                    .apply(lambda x: x.tz_convert('US/Eastern').tz_localize(None)))
            df_orders.rename(columns={'createTime': 'openTime'}, inplace=True)
            df_orders = df_orders[[
                'id', 'openTime', 'type', 'instrument', 'units', 'timeInForce', 'gtdTime', 'state',
                'stopLoss', 'trailingStopLoss', 'takeProfit', 'price'
            ]]
        else:
            df_orders = None

    # Trades
    headers = {'Authorization': 'Bearer ' + oanda_token}
    pricing_path = f'/v3/accounts/{oanda_acct}/trades'
    response = requests.get('https://' + oanda_url + pricing_path,
                            headers=headers
                            )
    print(f'Open Trades Response: {response.status_code}')

    if response.json()['trades'] == []:
        df_trades = None
    else:
        df_trades = pd.DataFrame(response.json()['trades'])
        df_trades.fillna('', inplace=True)

        try:
            df_trades['stopLoss'] = df_trades['stopLossOrder'].apply(lambda x: x['price'] if x != '' else None)
        except KeyError:
            df_trades['stopLoss'] = None
        try:
            df_trades['trailingStopLoss'] = (df_trades['trailingStopLossOrder']
                                             .apply(lambda x: x['distance'] if x != '' else None))
        except KeyError:
            df_trades['trailingStopLoss'] = None
        try:
            df_trades['takeProfit'] = df_trades['takeProfitOrder'].apply(lambda x: x['price'] if x != '' else None)
        except KeyError:
            df_trades['takeProfit'] = None

        df_trades.rename(columns={'currentUnits': 'units'}, inplace=True)
        df_trades = df_trades[[
            'id', 'openTime', 'instrument', 'units', 'state',
            'stopLoss', 'trailingStopLoss', 'takeProfit', 'price'
        ]]

    if df_orders is None and df_trades is None:
        print('No Open Trades')
        return pd.DataFrame()
    else:
        df = pd.concat([df_orders, df_trades])
        df.rename(columns={'price': 'currentPrice'}, inplace=True)
        df.replace({np.nan: None}, inplace=True)
        df['openTime'] = pd.to_datetime(df['openTime']).apply(lambda x: x.tz_convert('US/Eastern').tz_localize(None))
        print(f'{len(df)} Open Trades')
        return df
