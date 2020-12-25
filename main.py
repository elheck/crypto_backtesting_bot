import logging
import os
import datetime
from bot.executor.back_testing import BackTesting
from bot.indicator import Macd

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    back_testing_path = os.path.abspath("backtesting_data")
    macd = Macd()
    testing = BackTesting(back_testing_path, candle_time=15, visualize=True)
    testing.indicators.append(macd)

    results = testing.test_strategy(["XRPBTC"], datetime.datetime.now() - datetime.timedelta(days=10),
                                    datetime.datetime.now() - datetime.timedelta(hours=12))
