from google import genai
from google.genai import types
import pandas as pd

def fn_llm_chart_analysis(currency: str,
                          df_forex_factory: pd.DataFrame,
                          df_oanda_historical: pd.DataFrame,
                          df_oanda_pricing: pd.DataFrame,
                          gemini_token: str
                          ):

    currency_prompt = currency.replace('_', '')

    system_prompt = f'''
    You are a day trading expert in Forex Trading for a large financial organization. Your job is to analyze the {currency_prompt} and recommend profitable trades based on previous price action, upcoming news, and sentiment of the market. This includes an providing:
    - entry price
    - stop loss
    - profit target
    
    You are never to recommend any trades worth less than 25 pips.
    In addition to your reasoning, please provide a list exactly like "TRADING_ARRAY:[entry price, stop loss, profit target]"
    If no trade is recommended, please provide a list exactly like "TRADING_ARRAY:[0, 0, 0]".
    
    All times are in US/Eastern.
    '''

    user_prompt = f'''
    Please use the dataframe <df_forex_factory> to assist in your trade recommendations. This dataframe contains upcoming news for the week.
    <df_forex_factory>
    {df_forex_factory}
    </df_forex_factory>
    
    Please use the dataframe <df_oanda_historical> to assist in your trade recommendations. This dataframe contains historical price action in the form of candles (open, low, high, close) with timeframes specified in the `interval` field.
    <df_oanda_historical>
    {df_oanda_historical}
    </df_oanda_historical>
    
    Please take into account the current bid price, ask price, and spread in the <df_oanda_pricing> dataframe.
    <df_oanda_pricing>
    {df_oanda_pricing}
    </df_oanda_pricing>
    '''

    client = genai.Client(api_key=gemini_token)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.1
        )
    )
    print(response.status_code)
    print(response.content)
    return response.text


def fn_llm_chart_checkin(currency: str,
                         df_forex_factory: pd.DataFrame,
                         df_oanda_historical: pd.DataFrame,
                         df_oanda_pricing: pd.DataFrame,
                         df_open_trades: pd.DataFrame,
                         gemini_token: str
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
    Please use the dataframe <df_forex_factory> to assist in your recommendations. This dataframe contains upcoming news for the week.
    <df_forex_factory>
    {df_forex_factory}
    </df_forex_factory>

    Please use the dataframe <df_oanda_historical> to assist in your recommendation. This dataframe contains historical price action in the form of candles (open, low, high, close) with timeframes specified in the `interval` field.
    <df_oanda_historical>
    {df_oanda_historical}
    </df_oanda_historical>

    Please take into account the current bid price, ask price, and spread in the <df_oanda_pricing> dataframe.
    <df_oanda_pricing>
    {df_oanda_pricing}
    </df_oanda_pricing>
    
    Please use the dataframe <df_open_trades> to assist in your recommendation. This is a dataframe of the current trade open for {currency}.
    <df_open_trades>
    {df_open_trades}
    </df_open_trades>
    '''

    client = genai.Client(api_key=gemini_token)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.1
        )
    )
    return response.text
