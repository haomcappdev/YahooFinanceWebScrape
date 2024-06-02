from decimal import Decimal
from bs4 import BeautifulSoup
import os
import requests

def scrape_stock_info(stock_code, info):
    result = []
    url = f'https://finance.yahoo.com/quote/{stock_code}/key-statistics'
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')
        stock_price = soup.select_one(f'fin-streamer[data-field="regularMarketPrice"][data-symbol="{stock_code}"]')
        result.append(("Stock Price", stock_price.findAll("span")[0].string))
        for t in soup.select("table"):
            for tr in t.select("tr:has(td)"):
                for sup in tr.select("sup"):
                    sup.extract()
                tds = [td.get_text(strip=True) for td in tr.select("td")]
                if len(tds) == 2:
                    cleaned_column_title = tds[0].strip()
                    if cleaned_column_title in info:
                        result.append((cleaned_column_title, tds[1]))
                        if cleaned_column_title == "Diluted EPS (ttm)":
                            pe_ratio = get_price_to_earnings_ratio(stock_price, tds[1])
                            result.append(("Price to Earnings Ratio", pe_ratio))
    return result


def get_price_to_earnings_ratio(stock_price, earnings_per_share):
    if not stock_price and not earnings_per_share:
        return Decimal(stock_price) / Decimal(earnings_per_share)
    else:
        return ""


def write_stock_info_to_file(output_file_path, stock_code, stock_info_input):
    try:
        with open(output_file_path, "a") as file:
            file.write(stock_code)
            file.write('\n')
            for info in stock_info_input:
                file.write("{:<50} {}".format(*info))
                file.write('\n')
    except Exception as e:
        print("An error occurred:", str(e))


stock_codes = []
interested_info = []
output_file_path = "output.txt"
f = open("stock codes.txt", "r")
# f = open('C:\\Users\\Hao\\Documents\\Learning\\Python\\YahooFinanceWebScrape\\stock codes.txt', "r")
for line in f:
    stock_codes.append(line.strip())
f.close()
f = open("stock information", "r")
for line in f:
    interested_info.append(line.strip())
f.close()
if os.path.exists(output_file_path):
    os.remove(output_file_path)
for code in stock_codes:
    stock_info = scrape_stock_info(code, interested_info)
    write_stock_info_to_file(output_file_path, code, stock_info)
    print('\n')
