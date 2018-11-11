import time
import robinhood_api.authentication as auth
import robinhood_api.profiles as profiles
import robinhood_api.orders as orders
import robinhood_api.account as account
import robinhood_api.stocks as stocks
import datetime
import logging


def market_open_condition():
    date = datetime.datetime.now()

    # define market open time condition
    market_open_time = (4 >= date.weekday() >= 0 and
                        (date.hour >= 9 and date.minute > 30) and
                        (date.hour <= 3 and date.minute <= 59))

    return market_open_time


def code_execute_condition():
    date = datetime.datetime.now()

    # define code execution time condition
    code_execute_time = (date.hour >= 22 and date.hour <= 23)

    return code_execute_time


def main():
    # logging
    logger = logging.getLogger()
    console_logging = logging.StreamHandler()
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(name)s %(message)s',
                        filename='./log/myapp.log',
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

    while True:

        # check whether the market is open
        while market_open_condition():
            # check whether whether it is inside execution time
            if code_execute_condition():
                # check inventory
                my_stocks = account.build_holdings()

                # check whether the stock in the invertory is purchased today
                today_purchase_symbol_list = []
                previous_purchase_symbol_list = []

                for symbol in my_stocks.keys():
                    if datetime.datetime.now().date() == my_stocks[symbol]['last_transaction_at'].date():
                        today_purchase_symbol_list.append(symbol)
                    else:
                        previous_purchase_symbol_list.append(symbol)

                print("Today purchsed stocks: {stock_list}".format(stock_list=today_purchase_symbol_list))
                print("Previously purchsed stocks: {stock_list}".format(stock_list=previous_purchase_symbol_list))

                # execute strategy
                logger.info("Running strategy here")

                ## TODO
                # insert strategy here

                # wait and execute the whole process again
                logger.info("Strategy is executed. Will start over in {time_check_interval}".format(
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
