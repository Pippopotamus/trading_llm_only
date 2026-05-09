import time
import re
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

url = "https://www.forexfactory.com/calendar?week=this"
# url = "https://www.forexfactory.com/calendar?week=last"

# Mapping of Forex Factory element class names to semantic labels for parsing.
ALLOWED_ELEMENT_TYPES = {
    "calendar__cell": "date",  # Generic cell (used for date continuation rows)
    "calendar__cell calendar__date": "date",  # Date of the news event
    "calendar__cell calendar__time": "time",  # Time of the news event
    "calendar__cell calendar__currency": "currency",  # Affected currency
    "calendar__cell calendar__impact": "impact",  # Expected impact level (color-coded)
    "calendar__cell calendar__detail": "detail",  # Expected impact level (color-coded)
    "calendar__cell calendar__event event": "event",  # News event title
    "calendar__cell calendar__actual": "actual",  # Actual reported value
    "calendar__cell calendar__forecast": "forecast",  # Forecasted value
    "calendar__cell calendar__previous": "previous",  # Previously reported value
}


def fn_ff_scroll(driver):
    previous_position = None
    while True:
        current_position = driver.execute_script("return window.pageYOffset;")
        driver.execute_script("window.scrollTo(0, window.pageYOffset + 500);")
        time.sleep(2)
        if current_position == previous_position:
            break
        previous_position = current_position


def fn_ff_dates(text, type):
    # Full pattern: Day (e.g., Sun), Month (e.g., Jun), Day number (e.g., 1 or 01)
    pattern = r'\b(?P<day>Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b\s+' \
              r'(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b\s+' \
              r'(?P<date>\d{1,2})\b'

    match = re.search(pattern, text)
    if match:
        month_abbr = match.group("month")
        day = int(match.group("date"))

        # Convert month abbreviation to month number
        month_number = datetime.strptime(month_abbr, "%b").month

        # Format date as yyyy-mm-dd
        year = datetime.now().year
        formatted_date = f"{year}-{month_number:02d}-{day:02d}"

        if type == 'date':
            return formatted_date
        elif type == 'day':
            return match.group("day")
        else:
            return None
    else:
        return None


def fn_forex_factory():
    driver = webdriver.Chrome()
    driver.get(url)
    table = driver.find_element(By.CLASS_NAME, "calendar__table")
    data = []
    date_retained = ''
    time_retained = ''
    fn_ff_scroll(driver)

    for row in table.find_elements(By.TAG_NAME, "tr"):
        row_data = {}

        for element in row.find_elements(By.TAG_NAME, "td"):
            class_name = element.get_attribute('class')

            if 'calendar__cell calendar__date' == class_name:
                date_retained = element.text
            row_data['date'] = date_retained

            if 'calendar__cell calendar__time' == class_name:
                if element.text:
                    time_retained = element.text
            row_data['time'] = time_retained

            if (class_name in ALLOWED_ELEMENT_TYPES
                    and ALLOWED_ELEMENT_TYPES[class_name] != 'date'
                    and ALLOWED_ELEMENT_TYPES[class_name] != 'time'
                    and ALLOWED_ELEMENT_TYPES[class_name] != 'impact'):
                if element.text:
                    row_data[ALLOWED_ELEMENT_TYPES[class_name]] = element.text
            elif 'calendar__cell calendar__impact' == class_name:
                impact = ''
                for impact_element in element.find_elements(By.TAG_NAME, "span"):
                    impact = impact_element.get_attribute('title')

                row_data['impact'] = impact

        if len(row_data):
            data.append(row_data)

    driver.quit()

    df = pd.DataFrame(data)
    df.fillna("", inplace=True)
    df = df.loc[df['event'] != '']
    df['day_of_week'] = df['date'].apply(lambda x: fn_ff_dates(x, 'day'))
    df['date'] = df['date'].apply(lambda x: fn_ff_dates(x, 'date'))
    df['impact'] = df['impact'].apply(lambda x: x.replace(' Impact Expected', ''))
    df = df.iloc[:, [8, 0, 1, 2, 3, 4, 5, 6, 7]]
    df.reset_index(drop=True, inplace=True)

    return df
