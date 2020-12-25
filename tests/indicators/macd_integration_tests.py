import pandas as pd
from unittest import TestCase
from bot.indicator import Macd


class MacdTest(TestCase):

    def setUp(self) -> None:
        self.macd = Macd()

    def test_calculate_for_simple_case(self):
        a = [i for i in range(1, 1000)]
        df = pd.DataFrame(a)
        df2 = df.ewm(span=12).mean()
        df3 = df.ewm(span=26).mean()
        macd = df2 - df3
        signal = (df2-df3).ewm(span=9).mean()
        macd.columns = ["macd"]
        signal.columns = ["signal"]
        expected = pd.concat([macd, signal], axis=1)
        result = self.macd.calculate(a)
        self.assertEqual(result["signal"][745], expected["signal"][745])

