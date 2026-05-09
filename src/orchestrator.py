# orchestrator class
import pandas as pd
from datetime import datetime
from os.path import exists

import llm_chart_analysis
import trade
import oanda_pricing
import email_trade
from forex_factory import fn_forex_factory

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


def fn_currency_schedule(path_currency_schedule: str):
    df_currency_schedule = pd.read_csv(path_currency_schedule)
    current_hour = datetime.now().hour
    current_day = datetime.now().weekday()

    df_currency_schedule = df_currency_schedule[
        (df_currency_schedule['start_hour'] <= current_hour) &
        (df_currency_schedule['end_hour'] >= current_hour)]

    if current_day == 6 and current_hour >= 17:  # Sunday
        trading_day = True
    elif 0 <= current_day <= 3:  # Monday through Thursday
        trading_day = True
    elif current_day == 4 and current_hour < 17:  # Friday
        trading_day = True
    else:  # Weekend
        trading_day = False

    if trading_day:
        li_currencies = df_currency_schedule['currency'].tolist()
        print(f'Currencies currently available to trade: {li_currencies}')
    else:
        print('Not a trading day')
        li_currencies = []

    return df_currency_schedule, li_currencies


class Orchestrator:
    def __init__(self,
                 oanda_token: str,
                 oanda_acct: str,
                 oanda_url: str,
                 li_gemini_token: list,
                 model: str = "gemini-2.5-flash"):
        self.oanda_token = oanda_token
        self.oanda_acct = oanda_acct
        self.oanda_url = oanda_url
        self.li_gemini_token = li_gemini_token
        self.model = model

        self.llm_chart_analysis = (
            llm_chart_analysis.LLMChartAnalysis(li_gemini_token=self.li_gemini_token,
                                                model=self.model))
        self.oanda_pricing = (
            oanda_pricing.OandaPricing(oanda_token=self.oanda_token,
                                       oanda_url=self.oanda_url,
                                       oanda_acct=self.oanda_acct))
        self.oanda_trade = (
            trade.Trade(oanda_token=self.oanda_token,
                        oanda_url=self.oanda_url,
                        oanda_acct=self.oanda_acct))

        self.df_forex_factory = fn_forex_factory()

    def fn_trader(self,
                  currency: str,
                  path_trades: str,
                  df_currency_schedule: pd.DataFrame):

        print(f'\n--------------- {currency} ---------------')

        # Check for open orders
        df_open_orders = self.oanda_trade.fn_open_orders()

        if not df_open_orders.empty:
            li_open_orders = set(
                df_open_orders['instrument'].tolist())
        else:
            li_open_orders = []

        # Evaluate currency for a new trade
        if currency not in li_open_orders:
            print(f'No trade already open for {currency}')

            # Pull historical data
            df_oanda_historical = self.oanda_pricing.fn_oanda_historical(currency=currency)

            # Check current prices
            df_oanda_pricing = self.oanda_pricing.fn_oanda_current(currency=currency)

            # Analyze price action and news
            llm_response = self.llm_chart_analysis.fn_llm_chart_analysis(
                currency=currency,
                df_forex_factory=self.df_forex_factory,
                df_oanda_historical=df_oanda_historical,
                df_oanda_pricing=df_oanda_pricing,
            )

            # Place trade
            end_hour = df_currency_schedule[df_currency_schedule['currency'] == currency]['end_hour'].values[0]

            df_trade = (
                self.oanda_trade.fn_place_trade(
                    currency=currency,
                    response_llm=llm_response,
                    risk=0.01,
                    end_hour=end_hour,
                ))

            # Log trade
            df_trade['reasoning'] = llm_response
            df_trade.to_csv(
                f'{path_trades}trades.csv',
                mode='a',
                index=False,
                header=not exists(f'{path_trades}trades.csv')
            )

            email_trade.fn_email(currency=currency,
                                 response_llm=llm_response,
                                 model=self.model)

        # If trade is already open for currency
        else:
            print(f'Trade already open for {currency}')

        print('---------------------------------------')

    def fn_checkin(self,
                   path_forex_factory: str,
                   path_trades: str):

        # Check for open orders
        df_open_orders = self.oanda_trade.fn_open_orders()

        if not df_open_orders.empty:
            li_open_orders = set(df_open_orders['instrument'].tolist())
            print(f'Currently there are open trades for {li_open_orders}')
        else:
            print('No open trades')
            return None

        for currency in li_open_orders:
            print(f'\n--------------- {currency} ---------------')

            # Pull historical data
            df_oanda_historical = self.oanda_pricing.fn_oanda_historical(currency=currency)

            # Check current prices
            df_oanda_pricing = self.oanda_pricing.fn_oanda_current(currency=currency)

            llm_response = self.llm_chart_analysis.fn_llm_chart_checkin(
                currency=currency,
                df_forex_factory=self.df_forex_factory,
                df_oanda_historical=df_oanda_historical,
                df_oanda_pricing=df_oanda_pricing,
                df_open_trades=df_open_orders,
            )

            trade_id = df_open_orders[df_open_orders['instrument'] == currency]['id'].values[0]
            self.oanda_trade.fn_modify_trade(
                currency=currency,
                trade_id=trade_id,
                response_llm=llm_response
            )

            df_trade = pd.DataFrame([{
                'trade_id': trade_id,
                'instrument': currency,
                'reasoning': llm_response
            }])

            df_trade.to_csv(
                f'{path_trades}checkins.csv',
                mode='a',
                index=False,
                header=not exists(f'{path_trades}checkins.csv')
            )

            email_trade.fn_email(currency=currency,
                                 response_llm=llm_response,
                                 model=self.model)

            print('---------------------------------------')

        return None
