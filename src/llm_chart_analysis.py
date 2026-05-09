from google import genai
from google.genai import types
from time import sleep
import pandas as pd
import json
import csv

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)


class LLMChartAnalysis:
    def __init__(self,
                 li_gemini_token: list,
                 model: str):
        self.li_gemini_token = li_gemini_token
        self.model = model

    def fn_llm_chart_analysis(self,
                              currency: str,
                              df_forex_factory: pd.DataFrame,
                              df_oanda_historical: pd.DataFrame,
                              df_oanda_pricing: pd.DataFrame
                              ):
        currency_prompt = currency.replace('_', '')

        system_prompt = f'''
You are a day trading expert in Forex Trading for a large financial organization. Your job is to analyze the {currency_prompt} and recommend profitable trades based on previous price action, upcoming news, and sentiment of the market. This includes an providing:
- entry price
- stop loss
- profit target
- order type (MARKET or MARKET_IF_TOUCHED)

You are never to recommend any trades worth less than 20 pips and no more than half the daily average. The goal is to recommend profitable day trades, not swing trades.
It is better to provide no recommendation than a losing trade recommendation. Trading against the trend is not advised.

In addition to your reasoning, please provide a list exactly like "TRADING_ARRAY:[entry price, stop loss, profit target, 'order type']".
For `order type`, the options are:
- 'MARKET' to execute the trade at the current market price
- 'MARKET_IF_TOUCHED' to wait until entry price is reached

If the order type is 'MARKET_IF_TOUCHED', how long do you recommend to leave the order open for prior to cancellation?

If no trade is recommended, please provide a list exactly like "TRADING_ARRAY:[0, 0, 0, None]".

All times are in US/Eastern.

In addition to the trade recommendation, if there is any other information that could be provided to improve your analysis, please state it.
If there are any other related currency pairs you would like information on, please state those and their time frames as well.
If there is too much information or unnecessary information such as too many time frames for the currency pair, please state those.
'''

        user_prompt = f'''
Please use the csv <df_forex_factory> to assist in your trade recommendations. This csv contains upcoming news for the week.
<df_forex_factory>
{df_forex_factory.to_csv(index=False, quoting=csv.QUOTE_ALL)}
</df_forex_factory>

Please use the csv <df_oanda_historical> to assist in your trade recommendations. This csv contains historical price action in the form of candles (open, low, high, close) with timeframes specified in the `interval` field.
<df_oanda_historical>
{df_oanda_historical.to_csv(index=False, quoting=csv.QUOTE_ALL)}
</df_oanda_historical>

Please take into account the current bid price, ask price, and spread in the <df_oanda_pricing> csv.
<df_oanda_pricing>
{df_oanda_pricing.to_csv(index=False, quoting=csv.QUOTE_ALL)}
</df_oanda_pricing>
'''
        # print(user_prompt)
        i = 0
        client = genai.Client(api_key=self.li_gemini_token[i])

        iteration = 0
        while(iteration <= 6):
            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.1
                    )
                )
                print(response.status_code)
                print(response.content)
                return response.text
            except Exception as error:
                error_reason = (json.loads(json.dumps(error.details))
                    ['error']['details'][0]['violations'][0]['quotaId'])
                if 'Minute' in error_reason:
                    if iteration >= 6:
                        print('ERROR! With LLM')
                        print(error)
                        raise
                    iteration = iteration + 1
                    sleep(2**iteration)
                elif 'Day' in error_reason or 'Daily' in error_reason:
                    i = i + 1
                    if i <= len(self.li_gemini_token) - 1:
                        print(f'Changing to LLM {i}')
                        client = genai.Client(api_key=self.li_gemini_token[i])
                    else:
                        print('ERROR! Out of LLM tokens')
                        print(error)
                        raise


    def fn_llm_chart_checkin(self,
                             currency: str,
                             df_forex_factory: pd.DataFrame,
                             df_oanda_historical: pd.DataFrame,
                             df_oanda_pricing: pd.DataFrame,
                             df_open_trades: pd.DataFrame,
                             ):
        currency_prompt = currency.replace('_', '')

        system_prompt = f'''
You are a day trading expert in Forex Trading for a large financial organization. Your job is to analyze the open trade for {currency_prompt} and recommend whether to stay in the trade or exit the trade based on previous price action, upcoming news, and sentiment of the market.

In addition to your reasoning:
- If you recommend staying in the trade, provide exactly: "STAY_EXIT:['stay']"
- If you recommend exiting in the trade, provide exactly: "STAY_EXIT:['exit']"

All times are in US/Eastern.
'''

        user_prompt = f'''
Please use the csv <df_forex_factory> to assist in your recommendations. This csv contains upcoming news for the week.
<df_forex_factory>
{df_forex_factory.to_csv(index=False, quoting=csv.QUOTE_ALL)}
</df_forex_factory>

Please use the csv <df_oanda_historical> to assist in your recommendation. This csv contains historical price action in the form of candles (open, low, high, close) with timeframes specified in the `interval` field.
<df_oanda_historical>
{df_oanda_historical.to_csv(index=False, quoting=csv.QUOTE_ALL)}
</df_oanda_historical>
    
Please take into account the current bid price, ask price, and spread in the <df_oanda_pricing> csv.
<df_oanda_pricing>
{df_oanda_pricing.to_csv(index=False, quoting=csv.QUOTE_ALL)}
</df_oanda_pricing>

Please use the csv <df_open_trades> to assist in your recommendation. This is a csv of the current trade open for {currency}. The `state` field indicates whether the trade is open or pending. Pending orders are opened upon the actual price touching the entry price (Market At Price trades).
<df_open_trades>
{df_open_trades.to_csv(index=False, quoting=csv.QUOTE_ALL)}
</df_open_trades>
'''

        client = genai.Client(api_key=self.gemini_token)

        iteration = 0
        while(iteration <= 6):
            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.1
                    )
                )
                return response.text
            except:
                if iteration >= 6:
                    print('ERROR! With LLM')
                    return response.text
                iteration = iteration + 1
                sleep(2**iteration)
