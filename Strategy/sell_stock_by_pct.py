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
        if float(stock_inventory[stock_symbol]['price']) / float(
                stock_inventory[stock_symbol]['average_buy_price']) - 1 > pct_threshold_to_sell:

            orders.order_sell_market(symbol=stock_symbol,quantity=stock_inventory[stock_symbol]['quantity'])
            logger.info("Stock {stock_symbol} will be sold {units} at {current_price} with {average_buy_price}"
                        .format(stock_symbol=stock_symbol,
                                units=stock_inventory[stock_symbol]['quantity'],
                                current_price=float(stock_inventory[stock_symbol]['price']),
                                average_buy_price=float(
                                    stock_inventory[stock_symbol]['average_buy_price']))
                                )
        else:
            logger.info("Stock {stock_symbol} is not good to sell").format(stock_symbol=stock_symbol)
