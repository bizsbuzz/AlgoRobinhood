import robinhood_api.authentication as auth
import robinhood_api.stocks as stocks
import requests
from bs4 import BeautifulSoup
import datetime, pytz
import dateutil.parser
import datetime
import pandas as pd
import robinhood_api.account as account
import logging


def save_sp500_tickers():
    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text.rstrip("\n\r")
        tickers.append(ticker)

    return tickers


def download_news(login, symbol_list, date=datetime.datetime.now()):
    logger = logging.getLogger(__name__)

    # setup timestamp
    local_timezone = pytz.timezone("US/Eastern")
    start_time = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=0, minute=0, second=1)
    end_time = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=23, minute=59, second=59)

    news_dict = {}

    for symbol in symbol_list:
        logger.info('downloading news for symbol: {}'.format(symbol))
        # fetch news
        news = stocks.get_news(login=login, symbol=symbol)

        if len(news) == 0 or news[0] is None:
            continue

        for i in range(len(news)):
            news_line = news[i]

            # convert timestamp
            local_published_time = dateutil.parser.parse(news_line['published_at']).astimezone(local_timezone)

            # get news contents
            results = requests.get(news_line['url'])
            results_text = BeautifulSoup(results.text, "lxml")
            extract_text = results_text.find_all('p',
                                                 class_='canvas-atom canvas-text Mb(1.0em) Mb(0)--sm Mt(0.8em)--sm')
            contents = []
            for item in extract_text:
                final_text = item.get_text()
                contents.append(final_text)
            contents = list(set(contents))
            final_text = ''.join(contents)

            if local_published_time.timestamp() <= end_time.timestamp() and local_published_time.timestamp() >= start_time.timestamp():
                try:
                    news_dict['symbol'].append(symbol)
                    news_dict['timestamp'].append(local_published_time.strftime('%Y-%m-%d %H:%M'))
                    news_dict['title'].append(news_line['title'])
                    news_dict['source'].append(news_line['source'])
                    news_dict['url'].append(news_line['url'])
                    news_dict['contents'].append(final_text)
                except KeyError:
                    news_dict['symbol'] = [symbol]
                    news_dict['timestamp'] = [local_published_time.strftime('%Y-%m-%d %H:%M')]
                    news_dict['title'] = [news_line['title']]
                    news_dict['source'] = [news_line['source']]
                    news_dict['url'] = [news_line['url']]
                    news_dict['contents'] = [final_text]

    news_pd = pd.DataFrame.from_dict(news_dict)

    # save news to json
    news_pd.to_json('./data/news/news_json/news_{runid}.json'.format(runid=date.strftime("%Y%m%d%H%M%S")))

    return news_pd


def main():
    # take raw input including account id and password
    account_id = input("Enter your account id: ")
    pwd = input("Enter your password: ")

    # logging
    logger = logging.getLogger(__name__)
    console_logging = logging.StreamHandler()
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(name)s %(message)s',
                        filename='./log/news_downloader_log_{runid}.log'.format(
                            runid=datetime.datetime.now().strftime("%Y%m%d%H%M%S")),
                        filemode='w')
    formatter = logging.Formatter('%(asctime)s %(name)s %(message)s')
    console_logging.setFormatter(formatter)
    logger.addHandler(console_logging)

    # login account
    my_trader = auth.Robinhood()
    my_trader.login(username=account_id, password=pwd)
    logger.info("Successfully logged in account")

    # get watchlist
    watchlist_symbols = account.get_symbols_from_watchlist(login=my_trader)

    # executing news downloader
    logger.info("News downloader started at {execute_start_time}".format(
        execute_start_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    try:
        _ = download_news(login=my_trader, symbol_list=list(set(watchlist_symbols + save_sp500_tickers())),
                          date=datetime.datetime.now())
    except:
        logger.info("News downloader has error. Skip running.")

    logger.info("News downloader finished at {execute_start_time}".format(
        execute_start_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    # logout
    my_trader.logout()
    logger.info("Successfully logged out account.")


if __name__ == '__main__':
    main()
