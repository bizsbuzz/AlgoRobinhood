import logging
import robinhood_api.orders as orders
import robinhood_api.account as account


def buy_stop_loss_by_pct(stock_list, stock_inventory, pct_threshold_to_buy=0.05):
    """

    :param stock_list: a list of stock symbol
    :param stock_inventory: dict of stock inventory built from robinhood_api.account.build_holdings()
    :param pct_threshold_to_buy: double, where the current price is lower than buy price at this pct
    :return: none
    """

    logger = logging.getLogger(__name__)

    for stock_symbol in stock_list:

        stock_current_price = float(stock_inventory[stock_symbol]['price'])
        stock_average_buy_price = float(stock_inventory[stock_symbol]['average_buy_price'])
        stock_holding_units = float(stock_inventory[stock_symbol]['quantity'])

        # check the buying power and maximum buying quantity
        available_cash = float(account.build_user_profile()['cash'])

        # determine the quantity to buy to stop loss
        buying_quantity = max(int(stock_holding_units / 2.0), 1)
        total_purchased_price = float(buying_quantity) * stock_current_price

        if stock_current_price / stock_average_buy_price - 1 < (-1.0 * abs(pct_threshold_to_buy)):
            if total_purchased_price < available_cash:
                orders.order_buy_market(symbol=stock_symbol, quantity=buying_quantity, timeInForce='gfd')
                logger.info("Stock {stock_symbol} with units {units} current loss is {pct}% at current price: "
                            "${current_price} and average buying price: ${average_buy_price}."
                            .format(stock_symbol=stock_symbol,
                                    units=int(stock_holding_units),
                                    pct=round((stock_current_price / stock_average_buy_price - 1) * 100, 2),
                                    current_price=round(stock_current_price, 2),
                                    average_buy_price=round(stock_average_buy_price, 2)))
                logger.info(
                    "Stock {stock_symbol} will be purchased {units} units to reduce loss."
                        .format(stock_symbol=stock_symbol,
                                units=buying_quantity))
            else:
                logger.info("Stock {stock_symbol} with units {units} current loss is {pct}% at current price: "
                            "${current_price} and average buying price: ${average_buy_price}."
                            .format(stock_symbol=stock_symbol,
                                    units=int(stock_holding_units),
                                    pct=round((stock_current_price / stock_average_buy_price - 1) * 100, 2),
                                    current_price=round(stock_current_price, 2),
                                    average_buy_price=round(stock_average_buy_price, 2)))
                logger.info(
                    "Stock {stock_symbol} will NOT be purchased since you don't have sufficient cash ${cash}."
                        .format(stock_symbol=stock_symbol,
                                cash=round(available_cash, 2)))
