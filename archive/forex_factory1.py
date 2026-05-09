import requests
import pandas as pd
from os import path
from datetime import datetime

def fn_forex_factory_api():
    response = requests.get('https://nfs.faireconomy.media/ff_calendar_thisweek.json')
    df = pd.DataFrame(response.json())
    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
    return df


def fn_forex_factory(path_forex_factory):
    if path.exists(path_forex_factory):
        forex_factory_modified_time = datetime.fromtimestamp(path.getmtime(path_forex_factory))

        if forex_factory_modified_time.hour == datetime.now().hour:
            print('Forex Factory json exists and is unchanged')
            df = pd.read_json(path_forex_factory)
        else:
            print('Forex Factory json exists and has been recreated')
            df = fn_forex_factory_api()
            df.to_json(path_forex_factory)
    else:
        print('Forex Factory json does not exist')
        df = fn_forex_factory_api()
        df.to_json(path_forex_factory)

    return df
