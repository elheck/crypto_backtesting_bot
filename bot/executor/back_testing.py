import os
import logging
import datetime
from itertools import product
from typing import Iterable, Dict, List
from binance.client import Client
from pandas import DataFrame, read_pickle, Series
import seaborn as sns
from matplotlib import pyplot as plt
from bot.indicator import BUY_SELL
from bot.indicator.base_indicator import Signal

OPEN_TIME = 0
OPEN = 1
HIGH = 2
LOW = 3
CLOSE = 4
VOLUME = 5
CLOSE_TIME = 6
INTERVAL = Client.KLINE_INTERVAL_1MINUTE

UNIX_TIMESTAMP_FACTOR = 1000.0

HISTORY = "history"
INDICATOR = "indicator"


class BackTesting:

    def __init__(self, search_path, candle_time=1, visualize=False, starting_btc=1.0,
                 trade_fee_percent=0.1, max_buy_percent=20.0):
        self._indicators = list()
        self._candle_time = candle_time
        self._binance = Client("", "", "")
        self._visualize = visualize
        self._starting_money = starting_btc
        self._trade_fee_percent = trade_fee_percent
        self._max_buy_percent = max_buy_percent
        if os.path.isdir(search_path):
            self._search_path = search_path
        else:
            raise ValueError(f"{search_path} is not a folder")

    @property
    def candle_time(self):
        return self._candle_time

    @candle_time.setter
    def candle_time(self, value: int):
        self._candle_time = value

    @property
    def indicators(self):
        return self._indicators

    @indicators.setter
    def indicators(self, value):
        self._indicators = value

    def test_strategy(self, ticker: Iterable, start: datetime.datetime, end: datetime.datetime) -> Dict:
        data = {}
        for symbol in ticker:
            payload = {}
            history = self._get_historical_data(symbol, start, end)
            payload[HISTORY] = history
            indicator_data = self._get_indicator_data(history)
            payload[INDICATOR] = indicator_data
            data[symbol] = payload
        result_percentage = self._evaluate_strategy(data)
        if self._visualize:
            self._visualize_graph(data)
        return result_percentage

    def _visualize_graph(self, data: dict):
        logging.info("Visualizing...")
        sns.set_style("dark")
        for symbol, payload in data.items():
            time = payload[HISTORY].iloc(axis=1)[CLOSE_TIME].values.tolist()
            time = [datetime.datetime.fromtimestamp(stamp/UNIX_TIMESTAMP_FACTOR) for stamp in time]
            data = payload[HISTORY].iloc(axis=1)[CLOSE].apply(lambda x: float(x)).values.tolist()
            min_value = float(min(data))
            max_value = float(max(data))
            fig = plt.figure()
            number_indicators = len(self._indicators)
            current_plot_number = 1
            top_plot = fig.add_subplot(int(f"{number_indicators + 1}1{current_plot_number}"))
            buy_sell_columns = []
            for indicator_name, indicator_data in payload[INDICATOR].items():
                current_plot_number = current_plot_number + 1
                current_indicator_plot = fig.add_subplot(int(f"{number_indicators + 1}1{current_plot_number}"))
                for column_name, column_data in indicator_data.iteritems():
                    if column_name == BUY_SELL:
                        buy_sell_columns.append(column_data.tolist())
                    else:
                        current_indicator_plot.plot(time, column_data.apply(lambda x: float(x)).values.tolist(),
                                                    label=f"{indicator_name} - {column_name}")
                self._set_current_plot_configuration(current_indicator_plot, "Time", indicator_name)
            top_plot.plot(time, data, label=symbol)
            self._plot_buy_sell(top_plot, buy_sell_columns, time, min_value, max_value)
            self._set_top_plot_configuration(top_plot, symbol)
        plt.show()

    @staticmethod
    def _set_top_plot_configuration(top_plot: plt.Axes, symbol: str):
        top_plot.set_xlabel("Time")
        top_plot.set_ylabel(f"{symbol[-3:]}")
        top_plot.legend()
        top_plot.set_title(f"{symbol}")
        top_plot.grid()

    @staticmethod
    def _set_current_plot_configuration(plot: plt.Axes, x_label: str, title: str):
        plot.set_title(f"{title}")
        plot.set_xlabel(f"{x_label}")
        plot.grid()
        plot.legend()

    def _plot_buy_sell(self, top_plot: plt.Axes, all_buy_sell_data: List, time: List, y_min: float, y_max: float):
        buy_sell_consensus = self._get_buy_sell_consensus(all_buy_sell_data)
        buy_indices = buy_sell_consensus[buy_sell_consensus == Signal.buy].index
        sell_indices = buy_sell_consensus[buy_sell_consensus == Signal.sell].index
        buy_times = [time[index] for index in buy_indices]
        sell_times = [time[index] for index in sell_indices]
        top_plot.vlines(x=buy_times, ymax=y_max, ymin=y_min, ls='--', colors="green", label="buy")
        top_plot.vlines(x=sell_times, ymax=y_max, ymin=y_min, ls='--', colors="red", label="sell")

    @staticmethod
    def _get_buy_sell_consensus(all_buy_sell_data: List) -> Series:
        buy_sell_product = product(*all_buy_sell_data)
        consensus = []
        for index_values in buy_sell_product:
            if len(set(index_values)) == 1:
                consensus.append(index_values[0])
            else:
                consensus.append(Signal.none)
        return Series(consensus, dtype=object)

    def _get_historical_data(self, symbol: str, start: datetime.datetime, end: datetime.datetime) -> DataFrame:
        file_name = os.path.join(self._search_path, f"{symbol}.pkl")
        if os.path.isfile(file_name):
            data = self._get_historical_data_from_pickle_combined(symbol, start, end, file_name)
        else:
            data = self._get_historical_data_from_binance(symbol, start, end)
        data.to_pickle(file_name)
        return data[::self._candle_time]

    def _get_historical_data_from_pickle_combined(self, symbol: str, start: datetime.datetime, end: datetime.datetime,
                                                  file_name: str) -> DataFrame:
        logging.info(f"Getting historical data from {file_name}")
        data = read_pickle(file_name)
        first_timestamp_of_pickle = int(data[CLOSE_TIME].iloc[0])
        last_timestamp_of_pickle = int(data[CLOSE_TIME].iloc[-1])
        current_start = self._get_millis_from_datetime(start)
        current_end = self._get_millis_from_datetime(end)
        if first_timestamp_of_pickle > current_start:
            logging.info(f"Getting historical data from binance from before pickle data")
            prepending_data = self._binance.get_historical_klines(symbol, interval=INTERVAL, start_str=current_start,
                                                                  end_str=first_timestamp_of_pickle)
            prepending_df = DataFrame(prepending_data)
            data = prepending_df.append(data, ignore_index=True)
        if last_timestamp_of_pickle < current_end:
            logging.info(f"Getting historical data from binance from after pickle data")
            appending_data = self._binance.get_historical_klines(symbol, interval=INTERVAL,
                                                                 start_str=last_timestamp_of_pickle,
                                                                 end_str=current_end)
            appending_df = DataFrame(appending_data)
            data = data.append(appending_df, ignore_index=True)
        needed_data = data.loc[(data[0] >= current_start) & (data[0] <= current_end)]
        return needed_data

    def _get_historical_data_from_binance(self, symbol: str, start: datetime.datetime,
                                          end: datetime.datetime) -> DataFrame:
        data = []
        current_end = None
        for i in range((end - start).days):
            logging.info(f"Downloading data for {symbol} for day {i} of {(end - start).days - 1} days until {end}")
            current_start = self._get_millis_from_datetime(start + datetime.timedelta(days=i))
            current_end = self._get_millis_from_datetime(start + datetime.timedelta(days=i + 1))
            data = data + self._binance.get_historical_klines(symbol, interval=INTERVAL,
                                                              start_str=current_start, end_str=current_end)
        end_stamp = self._get_millis_from_datetime(end)
        data = data + self._binance.get_historical_klines(symbol, interval=INTERVAL,
                                                          start_str=current_end, end_str=end_stamp)
        return DataFrame(data)

    @staticmethod
    def _get_millis_from_datetime(time: datetime.datetime) -> int:
        return int(time.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)

    def _get_indicator_data(self, data: DataFrame) -> Dict[str, DataFrame]:
        indicator_data = {}
        try:
            for indicator in self._indicators:
                indicator_data[str(indicator)] = indicator.get_signal(data[CLOSE].values.tolist())
        except TypeError:
            raise ValueError("No/wrong indicators added to backtesting")
        return indicator_data

    def _evaluate_strategy(self, data: Dict) -> dict:
        result_dict = {}
        for ticker, ticker_data in data.items():
            result_dict[ticker] = {}
            history_data = ticker_data[HISTORY].iloc(axis=1)[CLOSE].apply(lambda x: float(x)).values.tolist()
            for indicator, indicator_data in ticker_data[INDICATOR].items():
                money = self._starting_money
                depot = 0.0
                for number, value in enumerate(indicator_data[BUY_SELL].tolist()):
                    if value == Signal.buy:
                        price = history_data[number]
                        spending = money * (self._max_buy_percent / 100.0)
                        spending_real = money * ((self._max_buy_percent - self._trade_fee_percent) / 100.0)
                        buy_volume = spending_real / price
                        money = money - spending
                        depot = depot + buy_volume
                    if value == Signal.sell and depot > 0.0:
                        price = history_data[number]
                        new_money = self._sell(money, depot, price)
                        depot = 0
                        money = new_money
                if depot > 0.0:
                    price = history_data[-1]
                    new_money = self._sell(money, depot, price)
                    money = new_money
                gain = money / self._starting_money
                result_dict[ticker][indicator] = gain
                logging.info(f"Results for {ticker} - {indicator}: gain={gain}, money={money} btc")
        return result_dict

    def _sell(self, money: float, depot: float, price: float):
        gross_sell_earnings = depot * price
        real_sell_earnings = gross_sell_earnings - (gross_sell_earnings *
                                                    (self._trade_fee_percent / 100.0))
        new_money = money + real_sell_earnings
        return new_money
