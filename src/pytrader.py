import orchestrator
import os
import sys
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime

# incorporate checkins (potentially use flash?)
# Tokens and URLs
li_gemini_token = [
    os.getenv('GEMINI_KEY1'),
    os.getenv('GEMINI_KEY2'),
    os.getenv('GEMINI_KEY3')
    ]

model = 'gemini-2.5-pro'
# model = 'gemini-2.5-flash'

# Practice Acct No: 8849037
oanda_acct = os.getenv('OANDA_ACCT')
oanda_token = os.getenv('OANDA_TOKEN')
oanda_url = 'api-fxpractice.oanda.com'

# Get working directory
cwd = os.getcwd()
cwd = 'C:\\Users\\mas58\\OneDrive\\Desktop\\Trades\\Test'
os.chdir(cwd)
# cwd = os.getcwd()

# path_forex_factory = f'{cwd}\\forex_factory.json'
path_currency_schedule = f'{cwd}\\currency_schedule.csv'
path_trades = f'{cwd}\\demo_'

start_time = datetime.now()

outfiles = {
    'stderr': cwd + '\\log_files\\' + str(start_time.strftime('%Y-%m-%d %H-%M-%S')) + '_stderr.txt',
    'stdout': cwd + '\\log_files\\' + str(start_time.strftime('%Y-%m-%d %H-%M-%S')) + '_stdout.txt',
}

if not os.path.isdir(cwd + '\\log_files'):
    os.mkdir(cwd + '\\log_files')

stdout_file = open(outfiles['stdout'], "w", buffering=1)
stderr_file = open(outfiles['stderr'], "w", buffering=1)

with redirect_stdout(stdout_file), redirect_stderr(stderr_file):
    print(f'Directory: {cwd}\n')

    try:
        df_currency_schedule, li_currencies = (
            orchestrator.fn_currency_schedule(path_currency_schedule))

        trader = orchestrator.Orchestrator(
            li_gemini_token=li_gemini_token,
            oanda_token=oanda_token,
            oanda_acct=oanda_acct,
            oanda_url=oanda_url,
            model=model
        )

        for currency in li_currencies:
            trader.fn_trader(
                  currency=currency,
                  path_trades=path_trades,
                  df_currency_schedule=df_currency_schedule
            )

        print(f'\nFinished: {datetime.now()}')

    except Exception as e:
        print(f"Caught exception:\n{e}", file=sys.stderr, flush=True)
