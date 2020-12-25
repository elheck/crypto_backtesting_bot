from typing import Iterable


INDICATORS = "indicators"
EXECUTOR = "executor"
MARKET = "market"
TICKER = "ticker"


class BotCreator:

    def __init__(self, **config):
        """
        kwargs:
            - market: str - Base market like "BTC"
            - executor: Executor - the executor which should execute this bot
            - indicators: Iterable[BaseIndicator] - An iterable of indicators that are already configured
            - ticker: Iterable[str] - An iterable of tickers which should be traded
        """
        self._market = self._evaluate_market(**config)
        self._executor = self._evaluate_executor(**config)
        self._indicators = self._evaluate_indicators(**config)
        self._ticker = self._evaluate_ticker(**config)

    @staticmethod
    def _evaluate_market(**config):
        if MARKET in config.keys():
            if not isinstance(config[MARKET], str):
                raise ValueError(f"{MARKET} is {type(config[MARKET])} not string type")
        else:
            raise AttributeError(f"{MARKET} is not in config")

    @staticmethod
    def _evaluate_executor(**config):
        if EXECUTOR in config.keys():
            if not isinstance(config[EXECUTOR], object):
                raise ValueError(f"Wrong executor type")
        else:
            raise AttributeError(f"{EXECUTOR} not in config")
        return config[EXECUTOR]

    @staticmethod
    def _evaluate_indicators(**config):
        if INDICATORS in config.keys():
            if isinstance(config[INDICATORS], Iterable):
                for indicator in config[INDICATORS]:
                    if not indicator.is_configured():
                        raise ValueError(f"{indicator} is not configured")
            else:
                raise ValueError(f"{config[INDICATORS]} is not an iterable")
        else:
            raise AttributeError(f"{INDICATORS} is not in config")
        return config[INDICATORS]

    @staticmethod
    def _evaluate_ticker(**config):
        if TICKER in config.keys():
            if not isinstance(config[TICKER], Iterable):
                raise ValueError(f"{TICKER} is {type(config[TICKER])} not iterable")
        else:
            raise AttributeError(f"{TICKER} is not in config")
