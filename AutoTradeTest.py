import time
import robinhood_api.authentication as auth
import robinhood_api.profiles as profiles
import robinhood_api.orders as orders
import robinhood_api.account as account
import robinhood_api.stocks as stocks
import datetime
import logging
import strategy.sell_stock_by_pct as sell_strategy
import strategy.buy_stock_recommendation_rating as recommendation


def market_open_condition():
    date = datetime.datetime.now()
    market_open_time = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=9, minute=30)
    market_close_time = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=16, minute=0)

    # define market open time condition
    market_open_time = (4 >= date.weekday() >= 0 and
                        (date > market_open_time) and
                        (date < market_close_time))

    return market_open_time
    # return True


def code_execute_condition():
    date = datetime.datetime.now()
    execution_start_time = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=7)
    execution_end_time = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=16, minute=0, second=1)

    # define code execution time condition
    code_execute_time = (date > execution_start_time and date < execution_end_time)

    return code_execute_time
    # return True


def main():
    # logging
    logger = logging.getLogger(__name__)
    console_logging = logging.StreamHandler()
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(name)s %(message)s',
                        filename='./log/execution_log_{runid}.log'.format(
                            runid=datetime.datetime.now().strftime("%Y%m%d%H%M%S")),
                        filemode='w')
    formatter = logging.Formatter('%(asctime)s %(name)s %(message)s')
    console_logging.setFormatter(formatter)
    logger.addHandler(console_logging)
    logger.info("Auto trading start at {execute_start_time}".format(execute_start_time=datetime.datetime.now()))

    # setup time interval of recursive checking
    time_check_interval = 30

    if code_execute_condition():
        logger.info(
            "The code is inside execution period, current time is {current_time}".format(
                current_time=datetime.datetime.now()))
    else:
        logger.info(
            "The code is outside execution period, current time is {current_time}".format(
                current_time=datetime.datetime.now()))
        return

    # login account
    auth.login(username='jiongxuan.zheng@gmail.com', password='Zjx134506@1')
    logger.info("Successfully logged in account")

    # train recommendation model and make recommendation for today
    _ = recommendation.buy_stock_recommend_rating(top=5)

    while True:

        # check whether the market is open
        while market_open_condition():
            # check whether whether it is inside execution time
            if code_execute_condition():
                # check inventory
                my_stocks = account.build_holdings()

                # check whether the stock in the inventory is transacted today
                today_transacted_symbol_list = []
                previous_transacted_symbol_list = []

                for symbol in my_stocks.keys():
                    if datetime.datetime.now().date() == my_stocks[symbol]['last_transaction_at'].date():
                        today_transacted_symbol_list.append(symbol)
                    else:
                        previous_transacted_symbol_list.append(symbol)

                logger.info("Today transacted stocks: {stock_list}".format(stock_list=today_transacted_symbol_list))
                logger.info(
                    "Previously transacted stocks: {stock_list}".format(stock_list=previous_transacted_symbol_list))

                # execute strategy
                logger.info("Running Strategy Algorithm now")

                ## TODO
                # insert buy strategy here

                # execute the sell operation
                sell_strategy.sell_by_pct(stock_list=previous_transacted_symbol_list,
                                          stock_inventory=my_stocks,
                                          pct_threshold_to_sell=0.02)

                # wait and execute the whole process again
                logger.info(
                    "Strategy Algorithm is executed. Will execute again in {time_check_interval} seconds".format(
                        time_check_interval=time_check_interval))
                time.sleep(time_check_interval)

            else:
                logger.info(
                    "The code is outside execution period, current time is {current_time}".format(
                        current_time=datetime.datetime.now()))
                # logout
                auth.logout()
                logger.info("Successfully logged out account")
                return

        else:
            # check whether whether it is inside execution time
            if code_execute_condition():
                logger.info("The market is closed, current time is {current_time}, "
                            "will check again in {interval} second".format(current_time=datetime.datetime.now().date(),
                                                                           interval=time_check_interval))
                time.sleep(time_check_interval)
            else:
                logger.info(
                    "The code is outside execution period, current time is {current_time}".format(
                        current_time=datetime.datetime.now()))
                # logout
                auth.logout()
                logger.info("Successfully logged out account")
                return


if __name__ == '__main__':
    main()
