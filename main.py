from bs4 import BeautifulSoup
import requests

def scrape_stock_info(stock_code, info):
    result = []
    url = f'https://finance.yahoo.com/quote/{stock_code}/key-statistics'
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')
        for t in soup.select("table"):
            for tr in t.select("tr:has(td)"):
                for sup in tr.select("sup"):
                    sup.extract()
                tds = [td.get_text(strip=True) for td in tr.select("td")]
                if len(tds) == 2:
                    cleaned_column_title = tds[0].strip()
                    if cleaned_column_title in info:
                        result.append((cleaned_column_title, tds[1]))
    return result


def log_stock_info(stock_info_input):
    for info in stock_info_input:
        print("{:<50} {}".format(*info))


stock_codes = []
interested_info = []
f = open("stock codes.txt", "r")
# f = open('C:\\Users\\Hao\\Documents\\Learning\\Python\\YahooFinanceWebScrape\\stock codes.txt', "r")
for line in f:
    stock_codes.append(line.strip())
f.close()
f = open("stock information", "r")
for line in f:
    interested_info.append(line.strip())
f.close()
for code in stock_codes:
    print(code)
    stock_info = scrape_stock_info(code, interested_info)
    log_stock_info(stock_info)
    print('\n')
