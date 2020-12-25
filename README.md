# crypto_bot

A first implementation of a crypto frequency trading bot.

* Currently only MACD as indicator and Backtesting as executor.
* This was used to test a specific indicator on historical data obtained through the binance public api.
* Saves historical data that it has obtained once as pickle and adds data to it if a larger timespan is needed.

It outputs a graph like this:
![Screenshot from 2020-12-25 22-11-53](https://user-images.githubusercontent.com/42242163/103142110-5bc1d800-46fe-11eb-9e3f-ff470a51acd5.png)

It also outputs a evaluation via logging like this 
![Screenshot from 2020-12-25 22-12-28](https://user-images.githubusercontent.com/42242163/103142111-5ebcc880-46fe-11eb-8109-0c4d3849081f.png)
