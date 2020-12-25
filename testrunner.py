import unittest
from tests.indicators.macd_integration_tests import MacdTest

TEST_CASES = [MacdTest]


def main():
    loader = unittest.TestLoader()
    tests = []
    for test_case in TEST_CASES:
        tests.append(loader.loadTestsFromTestCase(test_case))
    suite = unittest.TestSuite(tests)
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == "__main__":
    main()

