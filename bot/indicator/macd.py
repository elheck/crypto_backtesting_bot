import logging
import time
import pandas as pd
import numpy as np
from typing import Iterable, List
from .base_indicator import BaseIndicator, Signal, BUY_SELL


MACD = "macd"
SIGNAL = "signal"


class Macd(BaseIndicator):

    def __repr__(self):
        return "Macd"

    def __init__(self, ema_long: int = 26, ema_short: int = 12, signal_length: int = 9):
        super().__init__()
        self._ema_long = ema_long
        self._ema_short = ema_short
        self._signal_length = signal_length
        self._is_configured = True

    def calculate(self, data: Iterable) -> pd.DataFrame:
        df = pd.DataFrame(data)
        short_ema = df.ewm(span=self._ema_short).mean()
        long_ema = df.ewm(span=self._ema_long).mean()
        macd_line = short_ema - long_ema
        macd_line.columns = [MACD]
        signal_line = macd_line.ewm(span=self._signal_length).mean()
        signal_line.columns = [SIGNAL]
        result = pd.concat([macd_line, signal_line], axis=1)
        return result

    def get_signal(self, data: List):
        data = [float(x) for x in data]
        len_data = len(data)
        buy_sell_signals = []
        metric_data = pd.DataFrame()
        for _ in range(self._ema_long):
            metric_data = metric_data.append(pd.DataFrame({MACD: [0.0], SIGNAL: [0.0]}), ignore_index=True)
        start_time = time.time()
        initial_time = start_time
        for i in range(len_data - self._ema_long):
            last_position = self._ema_long + i
            if last_position % 1000 == 0:
                logging.info(f"Calculating MACD for data index up to {last_position} of {len_data - self._ema_long} "
                             f"took {time.time() - start_time} seconds")
                start_time = time.time()
            current_data = data[i: last_position]
            signal, metric = self._get_current_signal(current_data)
            last_values = metric.iloc[-1:]
            metric_data = metric_data.append(last_values, ignore_index=True)
            buy_sell_signals.append(signal)
        logging.info(f"Calculating MACD for the entire {len_data} data"
                     f"points took {(time.time() - initial_time)//60} minutes and {(time.time() - initial_time)%60} "
                     f"seconds")
        return self._combine_data(buy_sell_signals, metric_data)

    def _get_current_signal(self, data: Iterable):
        metric = self.calculate(data)
        current_macd = metric[MACD][metric.index[-1]]
        current_signal = metric[SIGNAL][metric.index[-1]]
        last_macd = metric[MACD][metric.index[-2]]
        last_signal = metric[SIGNAL][metric.index[-2]]
        if last_macd > last_signal and current_macd < current_signal:
            buy_sell_signal = Signal.sell
        elif last_macd < last_signal and current_macd > current_signal:
            buy_sell_signal = Signal.buy
        else:
            buy_sell_signal = Signal.none
        return buy_sell_signal, metric

    def _combine_data(self, signals: List, metrics: pd.DataFrame) -> pd.DataFrame:
        buy_sell = np.array([Signal.none for _ in range(len(metrics))], dtype=object)
        buy_sell_view = buy_sell[self._ema_long::]
        buy_sell_view[:] = np.array(signals, dtype=object)
        buy_sell[-1] = signals[-1]
        buy_sell_frame = pd.DataFrame({BUY_SELL: buy_sell})
        return pd.concat([metrics, buy_sell_frame], axis=1)
