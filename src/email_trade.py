import trade
import smtplib
from email.message import EmailMessage


def fn_email(currency,
             response_llm,
             model):
    if 'STAY_EXIT' in response_llm:
        stay_exit = trade.fn_extract_stay_exit(response_llm)
    else:
        stay_exit = ''
    if 'TRADING_ARRAY' in response_llm:
        trading_array = trade.fn_extract_trading_array(response_llm)
    else:
        trading_array = ''

    if stay_exit == 'stay':
        stay_exit_message = 'Stay in trade'
    elif stay_exit == 'exit':
        stay_exit_message = 'Exit trade'
    else:
        stay_exit_message = ''

    if trading_array != '':
        entry = trading_array[0]
        take_profit = trading_array[2]

        if entry > take_profit:
            buy_sell_message = 'Sell'
        elif entry < take_profit:
            buy_sell_message = 'Buy'
        else:
            buy_sell_message = ''
    else:
        buy_sell_message = ''

    if stay_exit_message == '' and buy_sell_message == '':
        buy_sell_message = 'No Trade'

    msg = EmailMessage()
    msg.set_content(f'{response_llm}')
    msg['Subject'] = f'{currency}: {stay_exit_message}{buy_sell_message} - {model}'
    msg['From'] = ""
    msg['To'] = ""

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login("", '')
        server.send_message(msg)

    return None
