from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

import requests
import sys

def scrape_stock_info(stock_code):
    result = []
    load_stock_name(stock_code)
    load_and_extract_from_key_statistics(result, stock_code)
    load_and_extract_from_balance_sheet(result, stock_code)
    load_and_extract_from_income_statement(result, stock_code)
    return result


def load_stock_name(stock_code):
    url = f'https://finance.yahoo.com/quote/{stock_code}/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')
        stock_name_tag = soup.select('h1[class="yf-xxbei9"]')
        print(stock_name_tag[0].text)


def load_and_extract_from_key_statistics(result, stock_code):
    url = f'https://finance.yahoo.com/quote/{stock_code}/key-statistics'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')
        extract_52_week_price(soup, result)
        extract_current_stock_price(soup, result)
        extract_trailing_dividend_yield(soup, result)
        extract_total_outstanding_shares(soup, result)
    return result


def load_and_extract_from_balance_sheet(result, stock_code):
    url = f'https://finance.yahoo.com/quote/{stock_code}/balance-sheet'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')
        extract_nav(soup, result)
    return result


def load_and_extract_from_income_statement(result, stock_code):
    url = f'https://finance.yahoo.com/quote/{stock_code}/financials'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')
        extract_eps(soup, result)
    return result


def extract_current_stock_price(soup, result):
    stock_price = soup.select('span[data-testid="qsp-price"]')

    if stock_price:
        result.append(("Stock Price", stock_price[0].text))
    else:
        result.append(("Stock Price", "Not found"))


def extract_trailing_dividend_yield(soup, result):
    columns = {'Trailing Annual Dividend Yield'}

    for t in soup.select("table"):
        for tr in t.select("tr:has(td)"):
            for sup in tr.select("sup"):
                sup.extract()
            tds = [td.get_text(strip=True) for td in tr.select("td")]
            if len(tds) == 2:
                cleaned_column_title = tds[0].strip()
                if cleaned_column_title in columns:
                    result.append((cleaned_column_title, tds[1]))
    return result


def extract_total_outstanding_shares(soup, result):
    columns = {'Shares Outstanding'}

    for t in soup.select("table"):
        for tr in t.select("tr:has(td)"):
            for sup in tr.select("sup"):
                sup.extract()
            tds = [td.get_text(strip=True) for td in tr.select("td")]
            if len(tds) == 2:
                cleaned_column_title = tds[0].strip()
                if cleaned_column_title in columns:
                    result.append((cleaned_column_title, tds[1]))
    return result


def extract_52_week_price(soup, result):
    columns = {'52 Week High', '52 Week Low'}

    for t in soup.select("table"):
        for tr in t.select("tr:has(td)"):
            for sup in tr.select("sup"):
                sup.extract()
            tds = [td.get_text(strip=True) for td in tr.select("td")]
            if len(tds) == 2:
                cleaned_column_title = tds[0].strip()
                if cleaned_column_title in columns:
                    result.append((cleaned_column_title, tds[1]))
    return result


def extract_nav(soup, result):
    tableItem = soup.select('div[class="column yf-t22klz alt"]')
    totalAssets = tableItem[0].text
    totalLiabilities = tableItem[2].text
    sharesOutstanding = result[4][1]

    # convert totalAssets to float
    totalAssetsFloat = float(format_thousandth_numeric_text(totalAssets))

    # convert totalLiabilities to flot
    totalLiabilitiesFloat = float(format_thousandth_numeric_text(totalLiabilities))

    # convert sharesOutstanding to float
    sharesOutstandingFloat = float(format_numeric_notation(sharesOutstanding))

    nav = round((totalAssetsFloat - totalLiabilitiesFloat)/sharesOutstandingFloat, 2)
    maxPriceByNAV = round(nav * 1.5, 2)
    result.append(("Net Asset Value", nav))
    result.append(("Net Asset Value x1.5 (current stock price should not exceed this value)", maxPriceByNAV))


def extract_eps(soup, result):
    epsAvailableYears = 3
    epsTag = soup.find(string="Basic EPS")
    epsRow = epsTag.parent.parent.parent
    oddColumns = epsRow.select('div[class="column yf-t22klz alt"]')
    evenColumns = epsRow.select('div[class="column yf-t22klz"]')
    # EPS may be  a "--" string value
    if (evenColumns[0].text.strip() != "--"):
        eps1YearAgo = float(evenColumns[0].text)
    else:
        eps1YearAgo = 0
        epsAvailableYears = epsAvailableYears - 1

    if (oddColumns[1].text.strip() != "--"):
        eps2YearsAgo = float(oddColumns[1].text)
    else:
        eps2YearsAgo = 0
        epsAvailableYears = epsAvailableYears - 1

    if (evenColumns[1].text.strip() != "--"):
        eps3YearsAgo = float(evenColumns[1].text)
    else:
        eps3YearsAgo = 0
        epsAvailableYears = epsAvailableYears - 1

    if (epsAvailableYears != 0):
        # fix division here
        averageEPS = round((eps1YearAgo + eps2YearsAgo + eps3YearsAgo) / epsAvailableYears, 2)
        maxPriceByEPS = round(((eps1YearAgo + eps2YearsAgo + eps3YearsAgo) / epsAvailableYears) * 15, 2)
        result.append((f"Average EPS ({epsAvailableYears} years)", averageEPS))
        result.append((f"Average EPS ({epsAvailableYears} years) x15 (current stock price should not exceed this value)", maxPriceByEPS))
    else:
        result.append(("Average EPS is not available", "--"))

def log_stock_info(stock_info_input):
    for info in stock_info_input:
        print("{:<50} {}".format(*info))


def format_thousandth_numeric_text(text):
    return text.replace(",", "").strip() + "000"


def format_numeric_notation(text):
    if 'B' in text:
        formattedText = float(text.replace('B', '')) * 1_000_000_000
    elif 'M' in text:
        formattedText = float(text.replace('M', '')) * 1_000_000
    else:
        formattedText = float(text)

    return formattedText


stock_codes = []
stockCodesFile = open("stock codes.txt", "r")
for line in stockCodesFile:
    stock_codes.append(line)
stockCodesFile.close()

folder = Path("Output")
folder.mkdir(parents=True, exist_ok=True)

now = datetime.now()
filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
file_path = folder / filename

original_stdout = sys.stdout
with file_path.open("w") as f:
    sys.stdout = f
    for code in stock_codes:
        stock_info = scrape_stock_info(code.strip().replace("\n", ""))
        log_stock_info(stock_info)
        print('\n')

# Restore original stdout
sys.stdout = original_stdout
print("Completed script.")
