import robinhood_api.stocks as stocks
import pandas as pd
import numpy as np
import pytz
import datetime
import dateutil.parser
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import logging
import numpy
from keras.models import Sequential
from keras.layers import Dense
import robinhood_api.account as account


def stock_rating(symbol, perf_window=5, label_pct_cutoff=0.05, historic_window=30, seed=7):
    """
    :param symbol: a string of symbol name
    :param perf_window: an integer of performance window that is used to define target label
    :param label_pct_cutoff: a double to define the threshold to label 1 when price go up by certain percentage
    :param historic_window: an integer of look back window which is used to define lagged features as predictors
    :param seed: random number seed
    :return: dictionary of {symbol: [model_forecast_prob, model_accuracy]}
    """
    logger = logging.getLogger(__name__)
    logger.info("Symbol {symbol} is using LSTM training model and doing forecast...".format(symbol=symbol))

    # fix random seed for reproducibility
    numpy.random.seed(seed)

    # get data
    price = stocks.get_historicals([symbol], span="year", interval="day", bounds='regular')
    price_data = pd.DataFrame.from_dict(price)
    price_data[['close_price', 'high_price', 'low_price', 'open_price', 'volume']] = price_data[
        ['close_price', 'high_price', 'low_price', 'open_price', 'volume']].apply(pd.to_numeric)

    # get average prive from high v.s. low
    price_data['avg_price'] = (price_data['high_price'] + price_data['low_price']) / 2

    # convert timestamp
    local_timezone = pytz.timezone("US/Eastern")
    price_data['timestamp'] = price_data['begins_at'].apply(dateutil.parser.parse)
    price_data['timestamp'] = price_data['timestamp'].dt.tz_convert(local_timezone).dt.strftime('%Y-%m-%d %H:%M')

    # define target variable
    price_data['rolling_max_avg_price'] = price_data['avg_price'].rolling(perf_window).max().shift(-perf_window)
    price_data['target_label'] = np.where(
        price_data['rolling_max_avg_price'] / price_data['avg_price'] - 1 > label_pct_cutoff, 1, 0)

    # create lag variable for model data
    model_data = price_data[['begins_at', 'timestamp', 'rolling_max_avg_price', 'target_label', 'avg_price']].copy()
    for i in range(1, historic_window + 1):
        exec("model_data['avg_price_lag%d'] = model_data['avg_price'].shift(%s)" % (i, i))

    model_data = model_data.dropna()

    # construct forecast data
    forecast_data = price_data[['begins_at', 'timestamp', 'avg_price']].copy()
    for i in range(1, historic_window + 1):
        exec("forecast_data['avg_price_lag%d'] = forecast_data['avg_price'].shift(%s)" % (i, i))

    forecast_data = forecast_data.tail(1)

    # Specify the data
    X = model_data.iloc[:, 4:]

    # Specify the target labels and flatten the array
    y = np.ravel(model_data.target_label)

    # Split the data up in train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=seed)

    X_forecast = forecast_data.iloc[:, 2:]

    # Define the scaler
    scaler = StandardScaler().fit(X_train)

    # Scale the train set
    X_train = scaler.transform(X_train)

    # Scale the test set
    X_test = scaler.transform(X_test)

    # Scale the forecast data
    X_forecast = scaler.transform(X_forecast)

    # Initialize the constructor
    model = Sequential()

    # Add an input layer
    model.add(Dense(12, activation='relu', input_shape=(len(X.columns),)))

    # Add one hidden layer
    model.add(Dense(8, activation='relu'))

    # Add an output layer
    model.add(Dense(1, activation='sigmoid'))

    # model fit
    model.compile(loss='binary_crossentropy',
                  optimizer='adam',
                  metrics=['accuracy'])

    model.fit(X_train, y_train, epochs=20, batch_size=1, verbose=0)

    # model performance
    score = model.evaluate(X_test, y_test, verbose=0)
    loss = score[0]
    accuracy = score[1]

    # forecast prediction
    y_forecast_pred = model.predict(X_forecast)

    logger.info(
        "Symbol {symbol} is trained and validated with accuracy {accuracy}%, forecasted to price up by {pct}% over the "
        "{days} days with predicted probability of {forecast_prob}%".format(
            symbol=symbol, accuracy=round(accuracy * 100, 2), pct=round(label_pct_cutoff * 100, 2), days=perf_window,
            forecast_prob=round(y_forecast_pred[0][0] * 100, 2)))

    return {symbol: [y_forecast_pred[0][0], accuracy]}


def buy_stock_recommend_rating(top=5, perf_threshold=0.8):
    """
    :param top: integer of showing top recommended stock in the log, ranked from high to low prob of price going up
    :param perf_threshold: double of only looking at models with performance >= the value
    :return: a list of top recommended {symbol: [model_forecast_prob, model_accuracy]}
    """
    # get watch list

    logger = logging.getLogger(__name__)

    watchlist_symbols = account.get_symbols_from_watchlist()

    rating = {}
    for symbol in watchlist_symbols:
        rating.update(stock_rating(symbol=symbol))

    rating_filter = {k: v for k, v in rating.items() if v[1] >= perf_threshold}
    rating_sorted = sorted(rating_filter.items(), key=lambda x: x[1][0], reverse=True)

    logger.info("Today's top {top} recommended stocks are: ".format(top=top))
    for i in rating_sorted[:top]:
        logger.info(
            "Symbol {symbol}: Rating {prob}% - Model Accuracy {accuracy}%".format(symbol=i[0],
                                                                                  prob=round(i[1][0] * 100, 2),
                                                                                  accuracy=round(i[1][1] * 100, 2)))

    return rating_sorted
