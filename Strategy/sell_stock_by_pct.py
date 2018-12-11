import logging
import robinhood_api.orders as orders


def sell_by_pct(stock_list, stock_inventory, pct_threshold_to_sell=0.02):
    """

    :param stock_list: a list of stock symbol
    :param stock_inventory: dict of stock inventory built from robinhood_api.account.build_holdings()
    :param pct_threshold_to_sell: double, where the current price is higher than buy price at this pct
    :return: none
    """

    logger = logging.getLogger(__name__)

    for stock_symbol in stock_list:

        stock_current_price = float(stock_inventory[stock_symbol]['price'])
        stock_average_buy_price = float(stock_inventory[stock_symbol]['average_buy_price'])
        stock_holding_units = float(stock_inventory[stock_symbol]['quantity'])

        if stock_current_price / stock_average_buy_price - 1 > pct_threshold_to_sell:

            orders.order_sell_market(symbol=stock_symbol, quantity=stock_holding_units)
            logger.info(
                "Stock {stock_symbol} will be sold {units} units at current price: {current_price} with average buying price: {average_buy_price}"
                    .format(stock_symbol=stock_symbol,
                            units=int(stock_holding_units),
                            current_price=round(stock_current_price, 2),
                            average_buy_price=round(stock_average_buy_price, 2))
            )
        else:
            logger.info(
                "Stock {stock_symbol} will NOT be sold {units} units at current price: {current_price} with average buying price: {average_buy_price}".format(
                    stock_symbol=stock_symbol,
                    units=int(stock_holding_units),
                    current_price=round(stock_current_price, 2),
                    average_buy_price=round(stock_average_buy_price, 2)))
