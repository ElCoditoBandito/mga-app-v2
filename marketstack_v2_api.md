# Marketstack API Documentation V2 - Easy Stock Data Integration

Welcome to the Marketstack API documentation. In the following series of articles, you will learn how to query the Marketstack JSON API for real-time, intraday, and historical stock market data, define multiple stock symbols, retrieve extensive data about 2700+ Stock Exchanges Info, 30000+ Stock tickers from more than 50 countries, as well as 750 + Stock Market indexes, information about timezones, currencies, and more.

Our API is built upon a RESTful and easy-to-understand request and response structure. API requests are always sent using a simple API request URL with a series of required and optional HTTPS GET parameters, and API responses are provided in lightweight JSON format. Continue below to get started, or click the blue button above to jump to our 3-Step Quickstart Guide.

!Run in postman

Fork collection into your workspace
-----------------------------------

Getting Started
---------------

### API Authentication

For every API request you make, you will need to make sure to be authenticated with the API by passing your API access key to the API's `access_key` parameter. You can find an example below.

**Example API Request:**

```
Request https://api.marketstack.com/v2/eod?access_key=YOUR_ACCESS_KEY&symbols=AAPL

```


**Important:** Please make sure not to expose your API access key publicly. If you believe your API access key may be compromised, you can always reset in your account dashboard.

### 256-bit HTTPS Encryption Available on: Free and any Paid Plans

If you're subscribed to either the free or any paid plans, you will be able to access the marketstack API using industry-standard HTTPS. To do that, simply use the `https` protocol when making API requests.

**Example API Request:**

```
https://api.marketstack.com/v2

```


  

### API Errors

API errors consist of error `code` and `message` response objects. If an error occurs, the marketstack will return HTTP status codes, such as `404` for "not found" errors. If your API request succeeds, status code `200` will be sent.

For validation errors, the marketstack API will also provide a `context` response object returning additional information about the error that occurred in the form of one or multiple sub-objects, each equipped with the name of the affected parameter as well as `key` and `message` objects. You can find an example error below.

**Example Error:**

```
{
   "error": {
      "code": "validation_error",
      "message": "Request failed with validation error",
      "context": {
         "symbols": [
            {
               "key": "missing_symbols",
               "message": "You did not specify any symbols."
            }
         ]
      }
   }
}

```


**Common API Errors:**

**Scroll left & right to navigate**



* Code: 401
  *  Type: Unauthorized
  *  Description: Check your access key or activity of the account
* Code: 403
  *  Type: https_access_restricted
  *  Description: HTTPS access is not supported on the current subscription plan.
* Code: 403
  *  Type: function_access_restricted
  *  Description: The given API endpoint is not supported on the current subscription plan.
* Code: 404
  *  Type: invalid_api_function
  *  Description: The given API endpoint does not exist.
* Code: 404
  *  Type: 404_not_found
  *  Description: Resource not found.
* Code: 429
  *  Type: too_many_requests
  *  Description: The given user account has reached its monthly allowed request volume.
* Code: 429
  *  Type: rate_limit_reached
  *  Description: The given user account has reached the rate limit.
* Code: 500
  *  Type: internal_error
  *  Description: An internal error occurred.


**Note:** The api is limited to 5 requests per second.

API Features
------------

### End-of-Day Data Available on: All plans

You can use the API's `eod` endpoint in order to obtain end-of-day data for one or multiple stock tickers. A single or multiple comma-separated ticker symbols are passed to the API using the `symbols` parameter.

**Note:** For a daily list of all tickers accessible via Marketstack, please see the following file which is updated daily.Download

**Note:** The V2 EOD endpoint supports information for 2700+ stock exchanges like the symbols from the NASDAQ, PINK, SHG, NYSE, NYSE ARCA, OTCQB, and BATS.

**Note:** To request end-of-day data for single ticker symbols, you can also use the API's Tickers Endpoint.

**Note:** Ticker Symbol Formatting - When searching for a ticker symbol with a period (.) in the name, in the intraday endpoint, please replace the period (.) with a hyphen (-). **Example:** For BRK.B, the correct format to use is BRK-B.

**Example API Request:**

```
Sign Up to Run API Requesthttps://api.marketstack.com/v2/eod
    ? access_key = YOUR_ACCESS_KEY
    & symbols = AAPL

```


**Endpoint Features:**

**Scroll left & right to navigate**



* Object: /eod/[date]
  * Description: Specify a date in YYYY-MM-DD format. You can also specify an exact time in ISO-8601 date format, e.g. 2020-05-21T00:00:00+0000. Example: /eod/2020-01-01
* Object: /eod/latest
  * Description: Obtain the latest available end-of-day data for one or multiple stock tickers.


**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: symbols
  * Description: [Required] Specify one or multiple comma-separated stock symbols (tickers) for your request, e.g. AAPL or AAPL,MSFT. Each symbol consumes one API request. Maximum: 100 symbols
* Object: exchange
  * Description: [Optional] Filter your results based on a specific stock exchange by specifying the MIC identification of a stock exchange. Example: XNAS
* Object: sort
  * Description: [Optional] By default, results are sorted by date/time descending. Use this parameter to specify a sorting order. Available values: DESC (Default), ASC.
* Object: date_from
  * Description: [Optional] Filter results based on a specific timeframe by passing a from-date in YYYY-MM-DD format. You can also specify an exact time in ISO-8601 date format, e.g. 2020-05-21T00:00:00+0000.
* Object: date_to
  * Description: [Optional] Filter results based on a specific timeframe by passing an end-date in YYYY-MM-DD format. You can also specify an exact time in ISO-8601 date format, e.g. 2020-05-21T00:00:00+0000.
* Object: limit
  * Description: [Optional] Specify a pagination limit (number of results per page) for your API request. Default limit value is 100, maximum allowed limit value is 1000.
* Object: offset
  * Description: [Optional] Specify a pagination offset value for your API request. Example: An offset value of 100 combined with a limit value of 10 would show results 100-110. Default value is 0, starting with the first available result. 


**Example API Response:**

If your API request was successful, the marketstack API will return both `pagination` information as well as a `data` object, which contains a separate sub-object for each requested date/time and symbol. All response objects are explained below.

```
{
    "pagination": {
      "limit": 100,
      "offset": 0,
      "count": 100,
      "total": 9944
    },
    "data": [
      {
        "open": 228.46,
        "high": 229.52,
        "low": 227.3,
        "close": 227.79,
        "volume": 34025967.0,
        "adj_high": 229.52,
        "adj_low": 227.3,
        "adj_close": 227.79,
        "adj_open": 228.46,
        "adj_volume": 34025967.0,
        "split_factor": 1.0,
        "dividend": 0.0,
        "name": "Apple Inc",
        "exchange_code": "NASDAQ",
        "asset_type": "Stock",
        "price_currency": "usd",
        "symbol": "AAPL",
        "exchange": "XNAS",
        "date": "2024-09-27T00:00:00+0000"
        },
      [...]
    ]
}

```


**API Response Objects:**

**Scroll left & right to navigate**



* Response Object: pagination > limit
  * Description: Returns your pagination limit value.
* Response Object: pagination > offset
  * Description: Returns your pagination offset value.
* Response Object: pagination > count
  * Description: Returns the results count on the current page.
* Response Object: pagination > total
  * Description: Returns the total count of results available.
* Response Object: date
  * Description: Returns the exact UTC date/time the given data was collected in ISO-8601 format.
* Response Object: symbol
  * Description: Returns the stock ticker symbol of the current data object.
* Response Object: exchange
  * Description: Returns the exchange MIC identification associated with the current data object.
* Response Object: split_factor
  * Description: Returns the split factor, which is used to adjust prices when a company splits, reverse splits, or pays a distribution.
* Response Object: dividend
  * Description: Returns the dividend, which are the distribution of earnings to shareholders.
* Response Object: open
  * Description: Returns the raw opening price of the given stock ticker.
* Response Object: high
  * Description: Returns the raw high price of the given stock ticker.
* Response Object: low
  * Description: Returns the raw low price of the given stock ticker.
* Response Object: close
  * Description: Returns the raw closing price of the given stock ticker.
* Response Object: volume
  * Description: Returns the raw volume of the given stock ticker.
* Response Object: adj_open
  * Description: Returns the adjusted opening price of the given stock ticker.
* Response Object: adj_high
  * Description: Returns the adjusted high price of the given stock ticker.
* Response Object: adj_low
  * Description: Returns the adjusted low price of the given stock ticker.
* Response Object: adj_close
  * Description: Returns the adjusted closing price of the given stock ticker.
* Response Object: adj_volume
  * Description: Returns the adjusted volume of given stock ticker.
* Response Object: name
  * Description: Returns the full-length name of the asset.
* Response Object: exchange_code
  * Description: Returns the identifier that maps which Exchange this asset is listed on.
* Response Object: asset_type
  * Description: Returns the asset type.
* Response Object: price_currency
  * Description: Returns the price currency.


**Adjusted Prices:** "Adjusted" prices are stock price values that were amended to accurately reflect the given stock's value after accounting for any corporate actions, such as splits or dividends. Adjustments are made in accordance with the "CRSP Calculations" methodology set forth by the Center for Research in Security Prices (CRSP).

### Intraday Data Available on: Basic Plan and higher

In additional to daily end-of-day stock prices, the marketstack API also supports intraday data with data intervals as short as one minute. **Intraday prices are available for all US stock tickers included in the IEX (Investors Exchange) stock exchange.**

To obtain intraday data, you can use the API's `intraday` endpoint and specify your preferred stock ticker symbols.

**Note:** For a daily list of all tickers accessible via Marketstack, please see the following file which is updated daily.Download

**Note:** To request intraday data for single ticker symbols, you can also use the API's Tickers Endpoint.

**Note:** Ticker Symbol Formatting - When searching for a ticker symbol with a period (.) in the name, in the intraday endpoint, please replace the period (.) with a hyphen (-). **Example:** For BRK.B, the correct format to use is BRK-B.

**IMPORTANT NOTE:** In the case of Intraday, Marketstack provides derived data that calculates a real-time reference price for each asset. While this is not a substitute for the TOPS Feed, we believe it will fulfill the needs of 95% of our customer base.

We’re doing so because as of **February 1st, 2025,** the IEX Exchange has changed its market data policies. To receive the FULL TOPS Feed, you must now have a market data agreement signed with the IEX Exchange. This means that the parameters bidPrice, bidSize, askPrice, askSize, lastPrice, lastSize, mid, and last will all return NULL in the API response for intraday since **IEX entitlement is required** for them. If you still need to have access to TOPS Feed, please contact our customer support team before signing any contract with them.

For using our derived data, there is no need to have a market data agreement signed with the IEX exchange, and there is no additional cost to the IEX Exchange.

**Example API Request:**

```

Sign Up to Run API Requesthttps://api.marketstack.com/v2/intraday
    ? access_key = YOUR_ACCESS_KEY
    & symbols = AAPL

```


**Endpoint Features:**

**Scroll left & right to navigate**



* Object: /intraday/[date]
  * Description: Specify a date in YYYY-MM-DD format. You can also specify an exact time in ISO-8601 date format, e.g. 2020-05-21T00:00:00+0000. Example: /intraday/2020-01-01
* Object: /intraday/latest
  * Description: Obtain the latest available intraday data for one or multiple stock tickers.


**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: symbols
  * Description: [Required] Specify one or multiple comma-separated stock symbols (tickers) for your request, e.g. AAPL or AAPL,MSFT. Each symbol consumes one API request. Maximum: 100 symbols
* Object: exchange
  * Description: [Optional] Filter your results based on a specific stock exchange by specifying the MIC identification of a stock exchange. Example: IEXG
* Object: interval
  * Description: [Optional] Specify your preferred data interval. Available values: 1min, 5min, 10min, 15min, 30min, 1hour (Default), 3hour, 6hour, 12hour and 24hour.
* Object: sort
  * Description: [Optional] By default, results are sorted by date/time descending. Use this parameter to specify a sorting order. Available values: DESC (Default), ASC.
* Object: date_from
  * Description: [Optional] Filter results based on a specific timeframe by passing a from-date in YYYY-MM-DD format. You can also specify an exact time in ISO-8601 date format, e.g. 2020-05-21T00:00:00+0000.
* Object: date_to
  * Description: [Optional] Filter results based on a specific timeframe by passing an end-date in YYYY-MM-DD format. You can also specify an exact time in ISO-8601 date format, e.g. 2020-05-21T00:00:00+0000.
* Object: limit
  * Description: [Optional] Specify a pagination limit (number of results per page) for your API request. Default limit value is 100, maximum allowed limit value is 1000.
* Object: offset
  * Description: [Optional] Specify a pagination offset value for your API request. Example: An offset value of 100 combined with a limit value of 10 would show results 100-110. Default value is 0, starting with the first available result. 
* Object: after_hours
  * Description: [Optional] If set to true, includes pre and post market data if available. By default is set to false.


**Real-Time Updates:** Please note that data frequency intervals below 15 minutes (`15min`) are only supported if you are subscribed to the Professional Plan or higher. If you are the Free or Basic Plan, please upgrade your account.

US equity markets close at 4 pm, anything 4 pm EST or after is considered after-market trades (>=). Example: the 19:59 on a 1-minute resample covers 19:59:00 to 19:59:59 (UTC), which is 3:59:00-3:59:59pm EST. Anything 4 pm or after will be after hours, which you can get as **after\_hours=true** when passing to the request. IEX does have limited after-hours trades though so data may be sparse at 4 pm and after.

​Keep in mind that the closing price is not the 4:00 pm EST price, most closing prices are an auction process https://www.investopedia.com/articles/investing/091113/auction-method-how-nyse-stock-prices-are-set.asp. You can get the EOD close via the EOD endpoints, but the closing price intraday is very different than the closing price EOD by convention (you are comparing last trade vs. auction close).

**Example API Response:**

If your API request was successful, the marketstack API will return both `pagination` information as well as a `data` object, which contains a separate sub-object for each requested date/time and symbol. All response objects are explained below.

```
{
    "pagination": {
        "limit": 100,
        "offset": 0,
        "count": 100,
        "total": 5000
    },
    "data": [
        {
          "open": 228.45,
          "high": 229.53,
          "low": 227.3,
          "mid": 227.28,
          "last_size": 6,
          "bid_size": 120.0,
          "bid_price": 227.02,
          "ask_price": 227.54,
          "ask_size": 100.0,
          "last": 227.54,
          "close": 227.52,
          "volume": 311345.0,
          "marketstack_last": 227.28,
          "date": "2024-09-27T16:00:00+0000",
          "symbol": "AAPL",
          "exchange": "IEXG"
        },
        [...]
    ]
}

```


**API Response Objects:**

**Scroll left & right to navigate**



* Response Object: pagination > limit
  * Description: Returns your pagination limit value.
* Response Object: pagination > offset
  * Description: Returns your pagination offset value.
* Response Object: pagination > count
  * Description: Returns the results count on the current page.
* Response Object: pagination > total
  * Description: Returns the total count of results available.
* Response Object: date
  * Description: Returns the exact UTC date/time the given data was collected in ISO-8601 format.
* Response Object: symbol
  * Description: Returns the stock ticker symbol of the current data object.
* Response Object: exchange
  * Description: Returns the exchange MIC identification associated with the current data object.
* Response Object: open
  * Description: The opening price of the asset on the current day. This value is calculated by Marketstack and not provided by IEX.
* Response Object: high
  * Description: The high price of the asset on the current day. This value is calculated by Marketstack and not provided by IEX.
* Response Object: low
  * Description: The low price of the asset on the current day. This value is calculated by Marketstack and not provided by IEX.
* Response Object: close
  * Description: Previous day's closing price of the security.This can be from any of the exchanges, NYSE, NASDAQ, IEX, etc
* Response Object: last
  * Description: Last is the last trade that was executed on IEX. IEX entitlement required
* Response Object: volume
  * Description: Volume will be IEX Volume throughout the day, but once the official closing price comes in, volume will reflect the volume done on the entire day across all exchanges. This field is available for convenience.
* Response Object: mid
  * Description:                                 Returns the mid price of the current timestamp when both "bidPrice" and "askPrice" are not-null. In mathematical terms: mid = (bidPrice + askPrice)/2.0. This value is calculated by Marketstack and not provided by IEX.                            
* Response Object: last_size
  * Description: The amount of shares traded (volume) at the last price on IEX. IEX entitlement required
* Response Object: bid_size
  * Description: The amount of shares at the bid price. IEX entitlement required
* Response Object: bid_price
  * Description: The current bid price. IEX entitlement required
* Response Object: ask_price
  * Description: The amount of shares at the ask price. IEX entitlement required
* Response Object: ask_size
  * Description: The current ask price. IEX entitlement required
* Response Object: marketstack_last
  * Description: Marketstack Last is either the last price or mid-price. The mid-price is only used if our algo determines it is a good proxy for the last price. So if the spread is considered wide by our algo, we do not use it. Also, after the official exchange print comes in, this value changes to that value. This value is calculated by Marketstack and not provided by IEX.                            


### Real-Time Updates Available on: Professional Plan and higher

For customers with an active subscription to the Professional Plan, the marketstack API's `intraday` endpoint is also capable of providing real-time market data, updated every minute, every 5 minutes or every 10 minutes.

To obtain real-time data using this endpoint, simply append the API's `interval` parameter and set it to `1min`, `5min` or `10min`.

**Example API Request:**

```

Sign Up to Run API Requesthttps://api.marketstack.com/v2/intraday
    ? access_key = YOUR_ACCESS_KEY
    & symbols = AAPL
    & interval = 1min

```


**Endpoint Features, Parameters & API Response:**

To learn about endpoint features, request parameters and API response objects, please navigate to the Intraday Data section.

### Commodity Prices Available for Professional and Higher plans

Get commodity prices of 70+ world-known commodities of energy, metals, industrial, agricultural, and livestock areas.

**Note:** Rate limit for 1 API call per minute is enforced on this endpoint. See the full list of available commodities in the file presented here: Download

**Example API Request:**

```

Sign Up to Run API Requesthttps://api.marketstack.com/v2/commodities
    ?access_key = YOUR_ACCESS_KEY
    &commodity_name = gold
```


**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: commodity_name
  * Description: [Required] Specify the commodity_name for which you like to receive the Price, e.g. aluminum. Each commodity consumes one API request.


If the Commodity is not supported, we will return an error message

`No Data Found for a Commodity (HTTP Status 404)`

```
{
    "detail": "The commodity is not found or no data is available. Please check the entered commodity and try again."
}

```


**Example API response:**

If your API request is successful, the marketstack API will return a data object, which contains an object with the commodity prices data. All response objects are explained below.

```
{
    "data": [
        {
            "commodity_name": "gold",
            "commodity_unit": "usd/t.oz",
            "commodity_price": "3014.79",
            "price_change_day": "8.86",
            "percentage_day": "-0.29%",
            "percentage_week": "0.48%",
            "percentage_month": "3.28%",
            "percentage_year": "38.80%",
            "quarter1_25": "3083.503",
            "quarter2_25": "3127.814",
            "quarter3_25": "3054.352",
            "quarter4_25": "3123.885",
            "datetime": "2025-03-24T15:42:00.000"
        }
    ]
}

```


**API Response Objects:**

**Scroll left & right to navigate**


|Response Object |Description                                                      |      |
|----------------|-----------------------------------------------------------------|------|
|commodity_name  |Returns the commodity name                                       |string|
|commodity_unit  |Returns the commodity unit                                       |string|
|commodity_price |Returns the commodity price                                      |string|
|price_change_day|Returns the commodity price change for the day                   |string|
|percentage_day  |Returns the percentage price change in a day                     |string|
|percentage_week |Returns the percentage price change in a week                    |string|
|percentage_month|Returns the percentage price change in a month                   |string|
|percentage_year |Returns the percentage price change in a year                    |string|
|quarter1_25     |Returns the commodity average price for a given quarter in a year|string|
|quarter2_25     |Returns the commodity average price for a given quarter in a year|string|
|quarter3_25     |Returns the commodity average price for a given quarter in a year|string|
|quarter4_25     |Returns the commodity average price for a given quarter in a year|string|
|datetime        |Returns the date and time                                        |string|


### Historical Data Available on: All plans

Historical stock prices are available both from the end-of-day (`eod`) and intraday (`intraday`) API endpoints. To obtain historical data, simply use the `date_from` and `date_to` parameters as shown in the example request below.

**Example API Request:**

```
Sign Up to Run API Requesthttps://api.marketstack.com/v2/eod
    ? access_key = YOUR_ACCESS_KEY
    & symbols = AAPL
    & date_from = 2025-05-04
    & date_to = 2025-05-14

```


**HTTPS GET Request Parameters:**

For details on request parameters on the `eod` data endpoint, please jump to the End-of-Day Data section.

**Example API Response:**

```
{
    "pagination": {
        "limit": 100,
        "offset": 0,
        "count": 22,
        "total": 22
    },
    "data": [
      {
        "open": 228.46,
        "high": 229.52,
        "low": 227.3,
        "close": 227.79,
        "volume": 34025967.0,
        "adj_high": 229.52,
        "adj_low": 227.3,
        "adj_close": 227.79,
        "adj_open": 228.46,
        "adj_volume": 34025967.0,
        "split_factor": 1.0,
        "dividend": 0.0,
        "name": "Apple Inc",
        "exchange_code": "NASDAQ",
        "asset_type": "Stock",
        "price_currency": "usd",
        "symbol": "AAPL",
        "exchange": "XNAS",
        "date": "2024-09-27T00:00:00+0000"
      }
        [...]
    ]
}

```


**API Response Objects:**

For details on API response objects, please jump to the End-of-Day Data section.

**Note:** Historical end-of-day data (`eod`) is available for up to 15 years back, while intraday data (`intraday`) always only offers the last 10,000 entries for each of the intervals available. Example: For a 1-minute interval, historical intraday data is available for up to 10,000 minutes back.

### Real-time Stock Market Prices Available for Professional and Higher plans

Real-time Stock Price API delivers instant access to live market data for stocks across major exchanges worldwide. Track intraday stock performance on `NYSE, NASDAQ, LON, WSE, EPA, SHE, NSE,` and much more. The full list can be seen here: Download

**Note:** There is a rate limitation for this endpoint, one API call per minute.

**Example API Request:**

```
Sign Up to Run API Requesthttps://api.marketstack.com/v2/stockprice
    ? access_key = YOUR_ACCESS_KEY
    &ticker=AAPL&exchange=nasdaq

```


**HTTPS GET Request Parameters:**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: ticker
  * Description: [Required] Specify the ticker for which you like to receive the Stock Price, e.g. AAPL. Each ticker consumes one API request.
* Object: exchange
  * Description: [Optional] Filter your results based on a specific stock exchange by specifying the MIC identification of a stock exchange. Example: NASDAQ


**Example API Response:**

If your API request is successful, the marketstack API will return a data object, which contains a separate sub-object for each exchange where the ticker symbol is available. All response objects are explained below.

```
{
    "data": [
        {
            "exchange_code": "NASDAQ",
            "exchange_name": "Nasdaq Stock Market",
            "country": "United States",
            "ticker": "AAPL",
            "price": "244.07",
            "currency": "USD",
            "trade_last": "2025-02-14 15:03:45"
        },
        {
            "exchange_code": "WSE",
            "exchange_name": "Warsaw Stock Exchange",
            "country": "Poland",
            "ticker": "AAPL",
            "price": "939.3",
            "currency": "PLN",
            "trade_last": "2025-02-12 11:01:42"
        }
    ]
}

```


**API Response Objects:**


|Response Object|Description                                                            |      |
|---------------|-----------------------------------------------------------------------|------|
|exchange_code  |Returns the exchange code                                              |string|
|exchange_name  |Returns the exchange name                                              |string|
|country        |Returns the exchange country                                           |string|
|ticker         |Returns the ticker info                                                |string|
|price          |Returns the last known price available from the exchange               |float |
|currency       |Returns the currency in which exchange operates, in which the price is.|string|
|trade_last     |Returns the date and time timestamp of the last known trade.           |string|


### Company ratings Available for Business and Higher plans

**Current Analyst Buy Sell Hold Ratings**

Classified as buy, sell and hold, the analyst ratings are immediately updated after analysts publish new equity research reports, which are added into our internal system for processing. The changes in the current ratings compared to the previous ratings will be applied to the data available through the analyst ratings API or via downloadable files.

**Historical Analyst ratings API**

_Buy Sell Hold and price consensus_

The historical analyst database maintains buy, sell, hold – ratings, recommendations and price targets from analysts for the last 15+ years. It allows customers to track the changes happening to an individual stock over time.The historical analyst ratings data can also be used to follow the success rate of an individual analyst over time and to draw conclusions about the quality of his/her rating.

**Note:** Rate limit is enforced to 1 API call per minute.

**Example API Request:**

```

Sign Up to Run API Requesthttps://api.marketstack.com/v2/companyratings
    ? access_key = YOUR_ACCESS_KEY
    &ticker=AAPL&date_to=2025-03-15&date_from=2025-01-01&rated=sell

```


**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
  *  :  string 
* Object: ticker
  * Description: [Required] Ticker Stock for which you want output
  *  :  string 
* Object: date_from
  * Description: [Optional] Used for getting historical ratings in a certain date range. Format YYYY-MM-DD
  *  :  string 
* Object: date_to
  * Description: [Optional] Used for getting historical ratings in a certain date range. Format YYYY-MM-DD
  *  :  string 
* Object: rated
  * Description: [Optional] In case you want to filter on buy, sell or hold. Acceptable values: sell, buy, hold
  *  :  string 


If the Ticker is not supported, we will return an error message

`No Data Found for a Commodity (HTTP Status 404)`

```
{
    "detail": "The ticker is not found or no data is available. Please check the entered ticker and try again."
}

```


**Example API Response:**

If your API request is successful, the marketstack API will return a data object, which contains an object with the Company Ratings data. All response objects are explained below.

```
{
    "status": {
        "code": 200,
        "message": "OK",
        "details": ""
    },
    "result": {
        "basics": {
            "company_name": "Apple Inc",
            "ticker": "AAPL"
        },
        "output": {
            "analyst_consensus": {
                "consensus_conclusion": "",
                "stock_price": "223.19",
                "analyst_average": "249.88",
                "analyst_highest": "325.00",
                "analyst_lowest": "188.00",
                "analysts_number": "30",
                "buy": "17",
                "hold": "9",
                "sell": "4",
                "consensus_date": "2025-04-01"
            },
            "analysts": [
                {
                    "analyst_name": "Brandon Nispel",
                    "analyst_firm": "KeyBanc",
                    "analyst_role": "analyst",
                    "rating": {
                        "date_rating": "2025-03-13",
                        "target_date": "2026-03-13",
                        "price_target": "200.0",
                        "rated": "Sell",
                        "conclusion": "reiterated"
                    }
                },
                {
                    "analyst_name": "Craig Moffett",
                    "analyst_firm": "MoffettNathanson",
                    "analyst_role": "analyst",
                    "rating": {
                        "date_rating": "2025-01-07",
                        "target_date": "2026-01-07",
                        "price_target": "188.0",
                        "rated": "Sell",
                        "conclusion": "downgraded"
                    }
                }
            ]
        }
    }
}

```


**API Response Objects:**

**Scroll left & right to navigate**



* Response Object: basics > company_name
  * Description: The name of the company.
  *  : string
* Response Object: basics > ticker
  * Description: The ticker symbol.
  *  : string
* Response Object: analyst_consensus > consensus_conclusion
  * Description: The average of all analysts in words: buy, hold, sell.
  *  : string
* Response Object: analyst_consensus > stock_price
  * Description: The price of the stock.
  *  : string
* Response Object: analyst_consensus > analyst_average
  * Description: Average price target of analysts with a 12 month price target
  *  : string
* Response Object: analyst_consensus > analyst_highest
  * Description: Highest rating of analysts
  *  : string
* Response Object: analyst_consensus > analyst_lowest
  * Description: Lowest rating of analysts
  *  : string
* Response Object: analyst_consensus > analysts_number
  * Description: The number of analysts participating in the analyses
  *  : string
* Response Object: analyst_consensus > buy
  * Description: Number of analysts with a Buy rating
  *  : string
* Response Object: analyst_consensus > sell
  * Description: Number of analysts with a Sell rating
  *  : string
* Response Object: analyst_consensus > hold
  * Description: Number of analysts with a Hold rating
  *  : string
* Response Object: analyst_consensus > consenuse_date
  * Description: The date when consensus is made.
  *  : string


### Splits Data Available on: All plans

Using the APIs`splits`endpoint you will be able to look up information about the stock splits factor for different symbols. You will be able to find and try out an example API request below.

To obtain splits data, you can use the API's `splits` endpoint and specify your preferred stock ticker symbols.

**Note:**The V2 Splits endpoint supports information about symbols from the NASDAQ, PINK, SHG, NYSE, NYSE ARCA, OTCQB, and BATS.

**Note:** To request splits data for single ticker symbols, you can also use the API's Tickers Endpoint.

**Example API Request:**

```

Sign Up to Run API Requesthttps://api.marketstack.com/v2/splits
    ? access_key = YOUR_ACCESS_KEY
    & symbols = AAPL

```


**Endpoint Features:**

**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: symbols
  * Description: [Required] Specify one or multiple comma-separated stock symbols (tickers) for your request, e.g. AAPL or AAPL,MSFT. Each symbol consumes one API request. Maximum: 100 symbols
* Object: sort
  * Description: [Optional] By default, results are sorted by date/time descending. Use this parameter to specify a sorting order. Available values: DESC (Default), ASC.
* Object: date_from
  * Description: [Optional] Filter results based on a specific timeframe by passing a from-date in YYYY-MM-DD format. You can also specify an exact time in ISO-8601 date format, e.g. 2020-05-21T00:00:00+0000.
* Object: date_to
  * Description: [Optional] Filter results based on a specific timeframe by passing an end-date in YYYY-MM-DD format. You can also specify an exact time in ISO-8601 date format, e.g. 2020-05-21T00:00:00+0000.
* Object: limit
  * Description: [Optional] Specify a pagination limit (number of results per page) for your API request. Default limit value is 100, maximum allowed limit value is 1000.
* Object: offset
  * Description: [Optional] Specify a pagination offset value for your API request. Example: An offset value of 100 combined with a limit value of 10 would show results 100-110. Default value is 0, starting with the first available result. 


**Example API Response:**

If your API request was successful, the marketstack API will return both `pagination` information as well as a `data` object, which contains a separate sub-object for each requested date/time and symbol. All response objects are explained below.

```
{
    "pagination": {
        "limit": 100,
        "offset": 0,
        "count": 100,
        "total": 50765
    },
    "data": [
        {
            "date": "2020-08-31",
            "split_factor": 4.0,
            "stock_split": "4:1",
            "symbol": "AAPL"
        },
        [...]
    ]
}

```


**API Response Objects:**

**Scroll left & right to navigate**



* Response Object: pagination > limit
  * Description: Returns your pagination limit value.
* Response Object: pagination > offset
  * Description: Returns your pagination offset value.
* Response Object: pagination > count
  * Description: Returns the results count on the current page.
* Response Object: pagination > total
  * Description: Returns the total count of results available.
* Response Object: date
  * Description: Returns the exact UTC date/time the given data was collected in ISO-8601 format.
* Response Object: symbol
  * Description: Returns the stock ticker symbol of the current data object.
* Response Object: split_factor
  * Description: Returns the split factor for that symbol on the date.
* Response Object: stock_split
  * Description: Returns the stock split.


### Commodities History Price Available for Professional and Higher plans

If you’re looking for past commodity prices, you can use the Historical Commodity Prices API, where you can choose specific dates and search by individual commodities. Additionally, the API offers options for daily data from the previous five years or monthly intervals using the ‘frequency’ parameter.

**Note:** Rate limit for 1 API call per minute is enforced on this endpoint.

**Note:** The historical date range can be 1 year in a single API call for daily data. 1,5 years also works, but for consistency, 1 year at a time is preferable.

The available historical data for Commodities is set up to 15 years in the past from the present day; however, not all commodities will have a full 15 years of data history.

*   Most of the metal commodities have historical coverage of more than 13 years, while only a few of them have historical coverage of 2 years.
*   Most of the energy commodities have historical coverage of 15 years, while a few of them have historical coverage of up to 10 years.
*   Industrial commodities have historical coverage of 15 years, while a few of them have historical coverage of up to 10 years
*   The livestock and agricultural commodities coverage is 9 to 15 years of historical data

**Example API Request:**

```

Sign Up to Run API Request https://api.marketstack.com/v2/commoditieshistory
    ? access_key = YOUR_ACCESS_KEY
    & commodity_name = aluminum

```


**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object:  access_key 
  * Description:  [Required]  Specify your API access key, available in your account dashboard.
* Object:  commodity_name 
  * Description:  [Required]  Specify the commodity_name for which you like to receive the Price, e.g. aluminum. Each commodity consumes one API request.
* Object: date_from
  * Description: [Optional] The beginning point of the date range within which you are searching for commodity prices.
* Object: date_to
  * Description: [Optional] The termination point of the date range within which you are searching for commodity prices.
* Object: frequency
  * Description: [Optional] The periodicity at which commodity prices are retrieved, can be day or month.


**If the Commodity is not supported, we will return an error message**

`No Data Found for a Commodity (HTTP Status 404)`

```
{
    "detail": "The commodity is not found or no data is available. Please check the entered commodity and try again."
}
```


**Example API Response:**

If your API request is successful, the marketstack API will return a `data` object, which contains an object with the commodities history prices data. All response objects are explained below.

```
"result": {
        "basics": {
            "frequency": "1day"
        },
"data": [
            {
                    "commodity_name": "brent",
                    "commodity_unit": "USD/Bbl",
                    "commodity_prices": [
                        {
                            "commodity_price": "94.75",
                            "date": "2010-12-31"
                        },
                        {
                            "commodity_price": "93.09",
                            "date": "2010-12-30"
                        },
                        {
                            "commodity_price": "94.14",
                            "date": "2010-12-29"
                        },
                        {
                            "commodity_price": "94.38",
                            "date": "2010-12-28"
                        },
                        {
                            "commodity_price": "93.85",
                            "date": "2010-12-27"
                        }
                    ]
            }
        ]
 }

"result": {
        "basics": {
            "frequency": "1month"
        },
"data": [
            {
                "commodity_name": "brent",
                "commodity_unit": "USD/Bbl",
                "commodity_prices": [
                    {
                        "commodity_price": "94.75",
                        "date": "2010-12"
                    },
                    {
                        "commodity_price": "93.09",
                        "date": "2010-11"
                    },
                    {
                        "commodity_price": "94.14",
                        "date": "2010-10"
                    },
                    {
                        "commodity_price": "94.38",
                        "date": "2010-09"
                    },
                    {
                        "commodity_price": "93.85",
                        "date": "2010-08"
                    }
                ]
            }
        ]
 }

```


**API Response Objects:**

**Scroll left & right to navigate**


|Response Object |Description                                   |      |
|----------------|----------------------------------------------|------|
|commodity_name  |Returns the commodity name                    |string|
|commodity_unit  |Returns the commodity unit                    |string|
|commodity_prices|Object holding the prices                     |string|
|commodity_price |Returns the commodity price                   |string|
|date            |Returns the date for the commodity price value|string|


### Dividends Data Available on: All plans

Using the APIs`dividends`endpoint you will be able to look up information about the stock dividend for different symbols. You will be able to find and try out an example API request below.

To obtain dividends data, you can use the API's `dividends` endpoint and specify your preferred stock ticker symbols.

**Note:** The V2 Dividend endpoint supports information about symbols from the NASDAQ, PINK, SHG, NYSE, NYSE ARCA, OTCQB, and BATS.

**Note:** To request dividends data for single ticker symbols, you can also use the API's Tickers Endpoint.

**Example API Request:**

```

Sign Up to Run API Requesthttps://api.marketstack.com/v2/dividends
    ? access_key = YOUR_ACCESS_KEY
    & symbols = AAPL

```


**Endpoint Features:**

**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: symbols
  * Description: [Required] Specify one or multiple comma-separated stock symbols (tickers) for your request, e.g. AAPL or AAPL,MSFT. Each symbol consumes one API request. Maximum: 100 symbols
* Object: sort
  * Description: [Optional] By default, results are sorted by date/time descending. Use this parameter to specify a sorting order. Available values: DESC (Default), ASC.
* Object: date_from
  * Description: [Optional] Filter results based on a specific timeframe by passing a from-date in YYYY-MM-DD format. You can also specify an exact time in ISO-8601 date format, e.g. 2020-05-21T00:00:00+0000.
* Object: date_to
  * Description: [Optional] Filter results based on a specific timeframe by passing an end-date in YYYY-MM-DD format. You can also specify an exact time in ISO-8601 date format, e.g. 2020-05-21T00:00:00+0000.
* Object: limit
  * Description: [Optional] Specify a pagination limit (number of results per page) for your API request. Default limit value is 100, maximum allowed limit value is 1000.
* Object: offset
  * Description: [Optional] Specify a pagination offset value for your API request. Example: An offset value of 100 combined with a limit value of 10 would show results 100-110. Default value is 0, starting with the first available result. 


**Example API Response:**

If your API request was successful, the marketstack API will return both `pagination` information as well as a `data` object, which contains a separate sub-object for each requested date/time and symbol. All response objects are explained below.

```
{
    "pagination": {
        "limit": 100,
        "offset": 0,
        "count": 100,
        "total": 50765
    },
    "data": [
        {
          "date": "2024-08-12",
          "dividend": 0.25,
          "payment_date": "2024-08-15 04:00:00",
          "record_date": "2024-08-12 04:00:00",
          "declaration_date": "2024-08-01 00:00:00",
          "distr_freq": "q",
          "symbol": "AAPL"
        },
        [...]
    ]
}

```


**API Response Objects:**

**Scroll left & right to navigate**



* Response Object: pagination > limit
  * Description: Returns your pagination limit value.
* Response Object: pagination > offset
  * Description: Returns your pagination offset value.
* Response Object: pagination > count
  * Description: Returns the results count on the current page.
* Response Object: pagination > total
  * Description: Returns the total count of results available.
* Response Object: date
  * Description: Returns the exact UTC date/time the given data was collected in ISO-8601 format.
* Response Object: symbol
  * Description: Returns the stock ticker symbol of the current data object.
* Response Object: dividend
  * Description: Returns the dividend for that symbol on the date.
* Response Object: payment_date
  * Description: Returns the payment date of the distribution.
* Response Object: record_date
  * Description: Returns the record date of the distribution.
* Response Object: declaration_date
  * Description: Returns the declaration date of the distribution.
* Response Object: distr_freq
  * Description: Returns the frequency that's associated with this distribution. For example "q" means quarterly, meaning this is a declared quarterly distribution. The full list of codes is available here: ● w: Weekly ● bm: Bimonthly ● m: Monthly ● tm: Trimesterly ● q: Quarterly ● sa: Semiannually ● a: Annually ● ir: Irregular ● f: Final ● u: Unspecified ● c: Cancelled 


### Tickers Available on: All plans

Using the API's `tickers` endpoint you will be able to look up information about one or multiple stock ticker symbols as well as obtain end-of-day, real-time and intraday market data for single tickers. You will be able to find and try out an example API request below.

**Example API Request:**

```

```


**Endpoint Features:**

**Scroll left & right to navigate**



* Object: /tickers/[symbol]
  * Description: Obtain information about a specific ticker symbol by attach it to your API request URL, e.g. /tickers/AAPL.
* Object: /tickers/[symbol]/eod
  * Description: Obtain end-of-day data for a specific stock ticker by attaching /eod to your URL, e.g. /tickers/AAPL/eod. This route supports parameters of the End-of-day Data endpoint.
* Object: /tickers/[symbol]/splits
  * Description: Obtain end-of-day data for a specific stock ticker by attaching /splits to your URL, e.g. /tickers/AAPL/splits. This route supports parameters like date period date_from and date_to and also you can sort the results DESC or ASC.
* Object: /tickers/[symbol]/dividends
  * Description: Obtain end-of-day data for a specific stock ticker by attaching /dividends to your URL, e.g. /tickers/AAPL/dividends. This route supports parameters like date period date_from and date_to and also you can sort the results DESC or ASC.
* Object: /tickers/[symbol]/intraday
  * Description: Obtain real-time & intraday data for a specific stock ticker by attaching /intraday to your URL, e.g. /tickers/AAPL/intraday. This route supports parameters of the Intraday Data endpoint.
* Object: /tickers/[symbol]/eod/[date]
  * Description: Specify a date in YYYY-MM-DD format. You can also specify an exact time in ISO-8601 date format, e.g. 2020-05-21T00:00:00+0000. Example: /eod/2020-01-01 or /intraday/2020-01-01
* Object: /tickers/[symbol]/eod/latest
  * Description: Obtain the latest end-of-day data for a given stock symbol. Example: /tickers/AAPL/eod/latest
* Object: /tickers/[symbol]/intraday/latest
  * Description: Obtain the latest intraday data for a given stock symbol. Example: /tickers/AAPL/intraday/latest


**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: exchange
  * Description: [Optional] To filter your results based on a specific stock exchange, use this parameter to specify the MIC identification of a stock exchange. Example: XNAS
* Object: limit
  * Description: [Optional] Specify a pagination limit (number of results per page) for your API request. Default limit value is 100, maximum allowed limit value is 1000.
* Object: offset
  * Description: [Optional] Specify a pagination offset value for your API request. Example: An offset value of 100 combined with a limit value of 10 would show results 100-110. Default value is 0, starting with the first available result. 


**API Response:**

```
{
    "name": "Apple Inc.",
    "symbol": "AAPL",
    "cik": "320193",
    "isin": "US0378331005",
    "cusip": "037833100",
    "ein_employer_id": "942404110",
    "lei": "HWUPKR0MPOU8FGXBT394",
    "series_id": "",
    "item_type": "equity",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "sic_code": "3571",
    "sic_name": "Electronic Computers",
    "stock_exchange": {
        "name": "NASDAQ - ALL MARKETS",
        "acronym": "NASDAQ",
        "mic": "XNAS",
        "country": null,
        "country_code": "US",
        "city": "NEW YORK",
        "website": "WWW.NASDAQ.COM",
        "operating_mic": "XNAS",
        "oprt_sgmt": "OPRT",
        "legal_entity_name": "",
        "exchange_lei": "",
        "market_category_code": "NSPD",
        "exchange_status": "ACTIVE",
        "date_creation": {
            "date": "2005-06-27 00:00:00.000000",
            "timezone_type": 1,
            "timezone": "+00:00"
        },
        "date_last_update": {
            "date": "2005-06-27 00:00:00.000000",
            "timezone_type": 1,
            "timezone": "+00:00"
        },
        "date_last_validation": {
            "date": "-0001-11-30 00:00:00.000000",
            "timezone_type": 1,
            "timezone": "+00:00"
        },
        "date_expiry": null,
        "comments": ""
    }
}

```


**API Response Objects:**

**Scroll left & right to navigate**



* Response Object: name
  * Description: Returns the name of the given stock ticker.
* Response Object: symbol
  * Description: Returns the symbol of the given stock ticker.
* Response Object: cik
  * Description: Returns the unique identifier assigned by the SEC to U.S. corporations and individuals for regulatory filings.
* Response Object: isin
  * Description: Returns the International Securities Identification Number.
* Response Object: cusip
  * Description: Returns the CUSIP number identifies most financial instruments, including: stocks of all registered U.S. and Canadian companies, commercial paper, and U.S. government and municipal bonds.
* Response Object: ein_employer_id
  * Description: Returns the unique nine-digit number that is assigned to a business entity.
* Response Object: lei
  * Description: Returns the Legal Entity Identifier.
* Response Object: series_id
  * Description: Returns the ID of the options series in which the stock option is.
* Response Object: item_type
  * Description: Returns the The type of the stock ticker.
* Response Object: sector
  * Description: Returns the Sector in which the company holding the stock ticker is.
* Response Object: industry
  * Description: Returns the Industry in which the company holding the stock ticker is.
* Response Object: sic_code
  * Description: Returns the Standard Industrial Clasification code.
* Response Object: sic_name
  * Description: Returns the Standard Industrial Clasification name.
* Response Object: stock_exchange > name
  * Description: Returns the name of the stock exchange associated with the given stock ticker.
* Response Object: stock_exchange > acronym
  * Description: Returns the acronym of the stock exchange associated with the given stock ticker.
* Response Object: stock_exchange > mic
  * Description: Returns the MIC identification of the stock exchange associated with the given stock ticker.
* Response Object: stock_exchange > country
  * Description: Returns the country of the stock exchange associated with the given stock ticker.
* Response Object: stock_exchange > country_code
  * Description: Returns the 3-letter country code of the stock exchange associated with the given stock ticker.
* Response Object: stock_exchange > city
  * Description: Returns the city of the stock exchange associated with the given stock ticker.
* Response Object: stock_exchange > website
  * Description: Returns the website URL of the stock exchange associated with the given stock ticker.
* Response Object: stock_exchange > operating_mic
  * Description: Returns the operating Market Identifier Code for the given stock ticker.
* Response Object: stock_exchange > oprt_sgmt
  * Description: Returns whether the MIC is an operating MIC or market segment MIC for the given stock ticker.
* Response Object: stock_exchange > legal_entity_name
  * Description: Returns the legal entity name for the given stock ticker.
* Response Object: stock_exchange > exchange_lei
  * Description: Returns the exchange Legal Entity Identifier for the given stock ticker.
* Response Object: stock_exchange > market_category_code
  * Description: Returns the market categoty code for the given stock ticker.
* Response Object: stock_exchange > exchange_status
  * Description: Returns the exchange status for the given stock ticker.
* Response Object: stock_exchange > date_creation > date
  * Description: Returns date creation date for the given stock ticker.
* Response Object: stock_exchange > date_creation > timezone_type
  * Description: Returns date creation timezone type for the given stock ticker.
* Response Object: stock_exchange > date_creation > timezone
  * Description: Returns date creation timezone for the given stock ticker.
* Response Object: stock_exchange > date_last_update > date
  * Description: Returns last date update for the given stock ticker.
* Response Object: stock_exchange > date_last_update > timezone_type
  * Description: Returns last date update timezone type for the given stock ticker.
* Response Object: stock_exchange > date_last_update > timezone
  * Description: Returns last date update timezone for the given stock ticker.
* Response Object: stock_exchange > date_last_validation > date
  * Description: Returns last date validation for the given stock ticker.
* Response Object: stock_exchange > date_last_validation > timezone_type
  * Description: Returns last date validation timezone type for the given stock ticker.
* Response Object: stock_exchange > date_last_validation > timezone
  * Description: Returns last date validation timezone for the given stock ticker.
* Response Object: stock_exchange > date_expiry
  * Description: Returns Expiry date for the given stock ticker.
* Response Object: stock_exchange > comments
  * Description: Returns comments for the given stock ticker.


### Tickers List Available on: All plans

Using the API's `tickerslist` endpoint you will be able to get the full list of supported tickers. You will be able to find and try out an example API request below.

**Example API Request:**

```

```


**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: search
  * Description: [Optional] Use this parameter to search stock tickers by name or ticker symbol.
* Object: exchange
  * Description: [Optional] Use this parameter to search stock tickers by the exchange mic.
* Object: limit
  * Description: [Optional] Specify a pagination limit (number of results per page) for your API request. Default limit value is 100, maximum allowed limit value is 1000.
* Object: offset
  * Description: [Optional] Specify a pagination offset value for your API request. Example: An offset value of 100 combined with a limit value of 10 would show results 100-110. Default value is 0, starting with the first available result. 


**API Response:**

```
{
    "pagination": {
        "limit": 100,
        "offset": 0,
        "count": 100,
        "total": 65510
    },
    "data": [
        {
            "name": "Microsoft Corporation",
            "ticker": "MSFT",
            "has_intraday": false,
            "has_eod": true,
            "stock_exchange": {
                "name": "NASDAQ - ALL MARKETS",
                "acronym": "NASDAQ",
                "mic": "XNAS"
            }
        },
        {
            "name": "Apple Inc",
            "ticker": "AAPL",
            "has_intraday": false,
            "has_eod": true,
            "stock_exchange": {
                "name": "NASDAQ - ALL MARKETS",
                "acronym": "NASDAQ",
                "mic": "XNAS"
            }
        },
        {
            "name": "Amazon.com  Inc",
            "ticker": "AMZN",
            "has_intraday": false,
            "has_eod": true,
            "stock_exchange": {
                "name": "NASDAQ - ALL MARKETS",
                "acronym": "NASDAQ",
                "mic": "XNAS"
            }
        },
        [...]
    ]
}

```


**API Response Objects:**

**Scroll left & right to navigate**



* Response Object: pagination > limit
  * Description: Returns your pagination limit value.
* Response Object: pagination > offset
  * Description: Returns your pagination offset value.
* Response Object: pagination > count
  * Description: Returns the results count on the current page.
* Response Object: pagination > total
  * Description: Returns the total count of results available.
* Response Object: name
  * Description: Returns the name of the given stock ticker.
* Response Object: ticker
  * Description: Returns the symbol of the given stock ticker.
* Response Object: has_intraday
  * Description: Returns information if there is a intraday data for the ticker available.
* Response Object: has_eod
  * Description: Returns information if there is a EOD data for the ticker available.
* Response Object: stock_exchange > name
  * Description: Returns the name of the given stock exchange.
* Response Object: stock_exchange > acronym
  * Description: Returns the acronym of the given stock exchange.
* Response Object: stock_exchange > mic
  * Description: Returns the MIC identification of the given stock exchange.


### Tickers Info Available on: All plans

Using the API's `tickerinfo` endpoint you will be able to look up information about tickers. You will be able to find and try out an example API request below.

**Example API Request:**

```

Sign Up to Run API Requesthttps://api.marketstack.com/v2/tickerinfo
    ? access_key = YOUR_ACCESS_KEY
    & ticker = MSFT

```


**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**


|Object    |Description                                                                 |
|----------|----------------------------------------------------------------------------|
|access_key|[Required] Specify your API access key, available in your account dashboard.|
|ticker    |[Required] To get results based on a ticker.                                |


**API Response:**

```
{
    "data": {
        "name": "MICROSOFT CORP",
        "ticker": "MSFT",
        "item_type": "equity",
        "sector": "Technology",
        "industry": "Software—Infrastructure",
        "exchange_code": "NMS",
        "full_time_employees": "221000",
        "ipo_date": null,
        "date_founded": null,
        "key_executives": [
            {
                "name": "Mr. Judson B. Althoff",
                "salary": "3.36M",
                "function": "Executive VP & Chief Commercial Officer",
                "exercised": "",
                "birth_year": "1974"
            },
            [....]
        ],
        "incorporation": "WA",
        "incorporation_description": "WA",
        "start_fiscal": null,
        "end_fiscal": "0630",
        "reporting_currency": null,
        "address": {
            "city": "REDMOND",
            "street1": "ONE MICROSOFT WAY",
            "street2": "",
            "postal_code": "98052-6399",
            "stateOrCountry": "WA",
            "state_or_country_description": "WA"
        },
        "post_address": {
            "city": "REDMOND",
            "street1": "ONE MICROSOFT WAY",
            "street2": "",
            "postal_code": "98052-6399",
            "stateOrCountry": "WA",
            "state_or_country_description": "WA"
        },
        "phone": "425-882-8080",
        "website": "https://www.microsoft.com",
        "previous_names": [],
        "about": "Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide. The company operates in three segments: Productivity and Business Processes, Intelligent Cloud, and More Personal Computing. The Productivity and Business Processes segment offers Office, Exchange, SharePoint, Microsoft Teams, Office 365 Security and Compliance, Microsoft Viva, and Skype for Business; Skype, Outlook.com, OneDrive, and LinkedIn; and Dynamics 365, a set of cloud-based and on-premises business solutions for organizations and enterprise divisions. The Intelligent Cloud segment licenses SQL, Windows Servers, Visual Studio, System Center, and related Client Access Licenses; GitHub that provides a collaboration platform and code hosting service for developers; Nuance provides healthcare and enterprise AI solutions; and Azure, a cloud platform. It also offers enterprise support, Microsoft consulting, and nuance professional services to assist customers in developing, deploying, and managing Microsoft server and desktop solutions; and training and certification on Microsoft products. The More Personal Computing segment provides Windows original equipment manufacturer (OEM) licensing and other non-volume licensing of the Windows operating system; Windows Commercial, such as volume licensing of the Windows operating system, Windows cloud services, and other Windows commercial offerings; patent licensing; and Windows Internet of Things. It also offers Surface, PC accessories, PCs, tablets, gaming and entertainment consoles, and other devices; Gaming, including Xbox hardware, and Xbox content and services; video games and third-party video game royalties; and Search, including Bing and Microsoft advertising. The company sells its products through OEMs, distributors, and resellers; and directly through digital marketplaces, online stores, and retail stores. Microsoft Corporation was founded in 1975 and is headquartered in Redmond, Washington.",
        "mission": null,
        "vision": null,
        "stock_exchanges": [
            {
                "city": "New York",
                "country": "USA",
                "website": "www.iextrading.com",
                "acronym1": "IEX",
                "alpha2_code": "US",
                "exchange_mic": "IEXG",
                "exchange_name": "Investors Exchange"
            },
            [....]
        ]
    }
}

```


**API Response Objects:**

**Scroll left & right to navigate**



* Response Object: name
  * Description: Returns the name of the ticker stock.
* Response Object: ticker
  * Description: Returns the symbol of the ticker stock.
* Response Object: item_type
  * Description: Returns the type of the stock.
* Response Object: sector
  * Description: Returns the sector in which the stock ticker is exist.
* Response Object: industry
  * Description: Returns the industry in which the stock ticker is exist.
* Response Object: exchange_code
  * Description: Returns the Exchange market code.
* Response Object: full_time_employees
  * Description: Returns the number of full employees in the company holding the ticker.
* Response Object: ipo_date
  * Description: Returns the date when the company stock went public.
* Response Object: date_founded
  * Description: Returns the date when the company is founded.
* Response Object: key_executives > name
  * Description: Returns the name of the key executive of the company.
* Response Object: key_executives > salary
  * Description: Returns the salary of the key executive of the company.
* Response Object: key_executives > function
  * Description: Returns the function of the key executive of the company.
* Response Object: key_executives > exercised
  * Description: Returns the exercised of the key executive of the company.
* Response Object: key_executives > birth_year
  * Description: Returns the bith year of the key executive of the company.
* Response Object: incorporation
  * Description: Returns the state of incorporation.
* Response Object: incorporation_description
  * Description: Returns the incorporation description.
* Response Object: start_fiscal
  * Description: Returns the start of a fiscal period.
* Response Object: end_fiscal
  * Description: Returns the end of a fiscal period.
* Response Object: reporting_currency
  * Description: Returns the reporting currency.
* Response Object: address > street1
  * Description: Returns the incorporation address of the company holding the ticker.
* Response Object: address > street2
  * Description: Returns the incorporation address of the company holding the ticker.
* Response Object: address > city
  * Description: Returns the incorporation city of the company holding the ticker.
* Response Object: address > stateOrCountry
  * Description: Returns the incorporation state or country of the company holding the ticker.
* Response Object: address > postal_code
  * Description: Returns the incorporation postal code of the company holding the ticker.
* Response Object: address > state_or_country_description
  * Description: Returns the incorporation state or country abbr of the company holding the ticker.
* Response Object: post_address > street1
  * Description: Returns the post address of the company holding the ticker.
* Response Object: post_address > street2
  * Description: Returns the post address of the company holding the ticker.
* Response Object: post_address > city
  * Description: Returns the post city of the company holding the ticker.
* Response Object: post_address > stateOrCountry
  * Description: Returns the post state or country of the company holding the ticker.
* Response Object: post_address > postal_code
  * Description: Returns the postal code of the company holding the ticker.
* Response Object: post_address > state_or_country_description
  * Description: Returns the post state or country abbr of the company holding the ticker.
* Response Object: phone
  * Description: Returns the phone number of the company.
* Response Object: website
  * Description: Returns the website of the company.
* Response Object: previous_names > name
  * Description: Returns previous name of the company.
* Response Object: previous_names > from
  * Description: Returns the date from when it was known by this name.
* Response Object: about
  * Description: Returns the about company details.
* Response Object: mission
  * Description: Returns the company mission.
* Response Object: vision
  * Description: Returns the company vision.
* Response Object: stock_exchanges > exchange_name
  * Description: Returns the exchange name of the ticker.
* Response Object: stock_exchanges > acronym1
  * Description: Returns the exchange acronym of the ticker.
* Response Object: stock_exchanges > exchange_mic
  * Description: Returns the exchange mic of the ticker.
* Response Object: stock_exchanges > country
  * Description: Returns the exchange country data of the ticker.
* Response Object: stock_exchanges > alpha2_code
  * Description: Returns the exchange alpha code of the ticker.
* Response Object: stock_exchanges > city
  * Description: Returns the exchange city of the ticker.
* Response Object: stock_exchanges > website
  * Description: Returns the exchange website of the ticker.


### Stock Market Index Listing Available on: Basic Plan and higher

The Stock Market Index API delivers instantly real-time and historical stock market index data. API End points return the full list of supported benchmarks/indexes.

The example API request below illustrates how to obtain data for the Stock market index.

**Example API Request:**

```

```


**Endpoint Features:**

**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: limit
  * Description: [Optional] Specify a pagination limit (number of results per page) for your API request. Default limit value is 100, maximum allowed limit value is 1000.
* Object: offset
  * Description: [Optional] Specify a pagination offset value for your API request. Example: An offset value of 100 combined with a limit value of 10 would show results 100-110. Default value is 0, starting with the first available result. 


**API Response:**

```
{
    "pagination": {
        "limit": 100,
        "offset": 0,
        "count": 86,
        "total": 86
    },
    "data": [
        {
            "benchmark": "adx_general"
        },
        {
            "benchmark": "ase"
        },
        {
            "benchmark": "aspi"
        },
        {
            "benchmark": "asx200"
        }
        [...]
    ]
}

```


**API Response Objects:**

**Scroll left & right to navigate**


|Response Object    |Description                                    |
|-------------------|-----------------------------------------------|
|pagination > limit |Returns your pagination limit value.           |
|pagination > offset|Returns your pagination offset value.          |
|pagination > count |Returns the results count on the current page. |
|pagination > total |Returns the total count of results available.  |
|benchmark          |Returns the benchmark code of the market index.|


  

### Stock Market Index Info Available on: Basic Plan and higher

The Stock Market Index API delivers instantly real-time and historical stock market index data Infrmaion. API End points return the details for the desired index.

The example API request below illustrates how to obtain data for the Stock market index Information.

**Example API Request:**

```

Sign Up to Run API Requesthttps://api.marketstack.com/v2/indexinfo
    ? access_key = YOUR_ACCESS_KEY
    & index = australia_all_ordinaries

```


**Endpoint Features:**

**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: index
  * Description: [Required] Specify your benchmark/index id for your request, e.g. australia_all_ordinaries.


**API Response:**

```
[
    {
        "benchmark": "australia all ordinaries",
        "region": "australia",
        "country": "australia",
        "price": "8553",
        "price_change_day": "71",
        "percentage_day": "0.84%",
        "percentage_week": "2.06%",
        "percentage_month": "1.13%",
        "percentage_year": "18.54%",
        "date": "2024-11-08"
    }
]

```


**API Response Objects:**

**Scroll left & right to navigate**


|Response Object |Description                                              |
|----------------|---------------------------------------------------------|
|benchmark       |Returns the benchmark of the market index.               |
|region          |Returns the region of the market index.                  |
|country         |Returns the country of the market index.                 |
|price           |Returns the current price of the market index.           |
|price_change_day|Returns the change of the price in a day.                |
|percentage_day  |Returns the change of the price in a day in percentage.  |
|percentage_week |Returns the change of the price in a week in percentage. |
|percentage_month|Returns the change of the price in a month in percentage.|
|percentage_year |Returns the benchmark code of the market index.          |
|date            |Returns the Current date.                                |


  

### Exchanges Available on: All plans

Using the `exchanges` API endpoint you will be able to look up information any of the 2700+ stock exchanges supported by this endpoint. This endpoint provides general information about several stock exchanges. Not all stock exchanges found here are supported by other Marketstack endpoints. For the supported stock exchanges supported by each endpoint, please verify each endpoint documentation. You will be able to find and try out an example API request below.

**Example API Request:**

```

```


**Endpoint Features:**

**Scroll left & right to navigate**



* Object: /exchanges/[mic]
  * Description: Obtain information about a specific stock exchange by attaching its MIC identification to your API request URL, e.g. /exchanges/XNAS.
* Object: /exchanges/[mic]/tickers
  * Description: Obtain all available tickers for a specific exchange by attaching the exchange MIC as well as /tickers, e.g. /exchanges/XNAS/tickers.
* Object: /exchanges/[mic]/eod
  * Description: Obtain end-of-day data for all available tickers from a specific exchange, e.g. /exchanges/XNAS/eod. For parameters, refer to End-of-day Data endpoint.
* Object: /exchanges/[mic]/intraday
  * Description: Obtain intraday data for tickers from a specific exchange, e.g. /exchanges/XNAS/intraday. For parameters, refer to Intraday Data endpoint.
* Object: /exchanges/[mic]/eod/[date]
  * Description: Obtain end-of-day data for a specific date in YYYY-MM-DD or ISO-8601 format. Example: /exchanges/XNAS/eod/2020-01-01.
* Object: /exchanges/[mic]/intraday/[date]
  * Description: Obtain intraday data for a specific date and time in YYYY-MM-DD or ISO-8601 format. Example: /exchanges/IEXG/intraday/2020-05-21T00:00:00+0000.
* Object: /exchanges/[mic]/eod/latest
  * Description: Obtain the latest end-of-day data for tickers of the given exchange. Example: /exchanges/XNAS/eod/latest
* Object: /exchanges/[mic]/intraday/latest
  * Description: Obtain the latest intraday data for tickers of the given exchange. Example: /exchanges/IEXG/intraday/latest


**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: search
  * Description: [Optional] Use this parameter to search stock exchanges by name or MIC.
* Object: limit
  * Description: [Optional] Specify a pagination limit (number of results per page) for your API request. Default limit value is 100, maximum allowed limit value is 1000.
* Object: offset
  * Description: [Optional] Specify a pagination offset value for your API request. Example: An offset value of 100 combined with a limit value of 10 would show results 100-110. Default value is 0, starting with the first available result. 


**API Response:**

```
{
    "pagination": {
        "limit": 100,
        "offset": 0,
        "count": 100,
        "total": 2700
    },
    "data": [
        {
          "name": "ALM. BRAND BANK",
          "acronym": "",
          "mic": "ABSI",
          "country": null,
          "country_code": "DK",
          "city": "COPENHAGEN",
          "website": "www.almbrand.dk",
          "operating_mic": "ABSI",
          "oprt_sgmt": "OPRT",
          "legal_entity_name": "",
          "exchange_lei": "2UM1RGHWEBOSN4PMNL63",
          "market_category_code": "SINT",
          "exchange_status": "ACTIVE",
          "date_creation": "2017-10-10",
          "date_last_update": "2017-10-10",
          "date_last_validation": "2017-10-10",
          "date_expiry": "2017-10-10",
          "comments": "SYSTEMATIC INTERNALISER."
        },
        [...]
    ]
}

```


**API Response Objects:**

**Scroll left & right to navigate**


|Response Object     |Description                                                            |
|--------------------|-----------------------------------------------------------------------|
|pagination > limit  |Returns your pagination limit value.                                   |
|pagination > offset |Returns your pagination offset value.                                  |
|pagination > count  |Returns the results count on the current page.                         |
|pagination > total  |Returns the total count of results available.                          |
|name                |Returns the name of the given stock exchange.                          |
|acronym             |Returns the acronym of the given stock exchange.                       |
|mic                 |Returns the MIC identification of the given stock exchange.            |
|country             |Returns the country of the given stock exchange.                       |
|country_code        |Returns the 3-letter country code of the given stock exchange.         |
|city                |Returns the given city of the stock exchange.                          |
|website             |Returns the website URL of the given stock exchange.                   |
|operating_mic       |Returns operating Market Identifier Code for the Exchange.             |
|oprt_sgmt           |Indicates whether the MIC is an operating MIC or a. market segment MIC.|
|legal_entity_name   |Returns the entity legal name.                                         |
|exchange_lei        |Returns the exchange Legal Entity Identifier.                          |
|market_category_code|Returns the category code of the market.                               |
|exchange_status     |Returns current status of the Exchange.                                |
|date_creation       |Returns date when the Exchange is created.                             |
|date_last_update    |Returns the date when the Exchange was last updated.                   |
|date_last_validation|Returns the date when the Exchange was last validated.                 |
|date_expiry         |Returns the date when the Exchange is expiring.                        |
|comments            |Returns any comments for the Exchange.                                 |


### Currencies Available on: All plans

Using the `currencies` API endpoint you will be able to look up all currencies supported by the marketstack API. You will be able to find and try out an example API request below.

**Example API Request:**

```

```


**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: limit
  * Description: [Optional] Specify a pagination limit (number of results per page) for your API request. Default limit value is 100, maximum allowed limit value is 1000.
* Object: offset
  * Description: [Optional] Specify a pagination offset value for your API request. Example: An offset value of 100 combined with a limit value of 10 would show results 100-110. Default value is 0, starting with the first available result. 


**API Response:**

```
{
    "pagination": {
        "limit": 100,
        "offset": 0,
        "count": 40,
        "total": 40
    },
    "data": [
        {
            "code": "USD",
            "name": "US Dollar",
            "symbol": "$",
            "symbol_native": "$",
        },
        [...]
    ]
}

```


**API Response Objects:**

**Scroll left & right to navigate**


|Response Object    |Description                                          |
|-------------------|-----------------------------------------------------|
|pagination > limit |Returns your pagination limit value.                 |
|pagination > offset|Returns your pagination offset value.                |
|pagination > count |Returns the results count on the current page.       |
|pagination > total |Returns the total count of results available.        |
|code               |Returns the 3-letter code of the given currency.     |
|name               |Returns the name of the given currency.              |
|symbol             |Returns the text symbol of the given currency.       |
|symbol_native      |Returns the native text symbol of the given currency.|


### Timezones Available on: All plans

Using the `timezones` API endpoint you will be able to look up information about all supported timezones. You will be able to find and try out an example API request below.

**Example API Request:**

```

```


**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: limit
  * Description: [Optional] Specify a pagination limit (number of results per page) for your API request. Default limit value is 100, maximum allowed limit value is 1000.
* Object: offset
  * Description: [Optional] Specify a pagination offset value for your API request. Example: An offset value of 100 combined with a limit value of 10 would show results 100-110. Default value is 0, starting with the first available result. 


**API Response:**

```
{
    "pagination": {
        "limit": 100,
        "offset": 0,
        "count": 57,
        "total": 57
    },
    "data": [
        {
            "timezone": "America/New_York",
            "abbr": "EST",
            "abbr_dst": "EDT"
        },
        [...]
    ]
}

```


**API Response Objects:**

**Scroll left & right to navigate**


|Response Object    |Description                                                |
|-------------------|-----------------------------------------------------------|
|pagination > limit |Returns your pagination limit value.                       |
|pagination > offset|Returns your pagination offset value.                      |
|pagination > count |Returns the results count on the current page.             |
|pagination > total |Returns the total count of results available.              |
|timezone           |Returns the name of the given timezone.                    |
|abbr               |Returns the abbreviation of the given timezone.            |
|abbr_dst           |Returns the Summer time abbreviation of the given timezone.|


### Bonds Listing Available on: Basic Plan and higher

The Bonds Listing API delivers the list of the supported countries data. API End points return the full list of supported countries.

The example API request below illustrates how to obtain for the bonds.

**Example API Request:**

```

```


**Endpoint Features:**

**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: limit
  * Description: [Optional] Specify a pagination limit (number of results per page) for your API request. Default limit value is 100, maximum allowed limit value is 1000.
* Object: offset
  * Description: [Optional] Specify a pagination offset value for your API request. Example: An offset value of 100 combined with a limit value of 10 would show results 100-110. Default value is 0, starting with the first available result. 


**API Response:**

```
{
    "pagination": {
        "limit": 100,
        "offset": 0,
        "count": 53,
        "total": 53
    },
    "data": [
        {
            "country": "austria"
        },
        {
            "country": "australia"
        },
        {
            "country": "belgium"
        },
        {
            "country": "brazil"
        }
        [...]
    ]
}

```


**API Response Objects:**

**Scroll left & right to navigate**


|Response Object    |Description                                   |
|-------------------|----------------------------------------------|
|pagination > limit |Returns your pagination limit value.          |
|pagination > offset|Returns your pagination offset value.         |
|pagination > count |Returns the results count on the current page.|
|pagination > total |Returns the total count of results available. |
|country            |Returns the name of the country.              |


  

### Bond Info Available on: Basic Plan and higher

The Bond API delivers immediately real-time government bond data. The bond data focuses on treasury notes issued in leading countries worldwide for ten years. The Bond API delivers info for every country. API End points return the details for the desired country.

The example API request below illustrates how to obtain conuntry data for the Bonds.

**Example API Request:**

```

Sign Up to Run API Requesthttps://api.marketstack.com/v2/bond
    ? access_key = YOUR_ACCESS_KEY
    & country = kenya

```


**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**


|Object    |Description                                                                    |
|----------|-------------------------------------------------------------------------------|
|access_key|[Required] Specify your API access key, available in your account dashboard.   |
|country   |[Required] Specify your country for your request, e.g. kenya or united%20states|


**API Response:**

```
{
    "pagination": {
        "limit": 100,
        "offset": 0,
        "count": 1,
        "total": 1
    },
    "data": [
        {
            "region": "africa",
            "country": "kenya",
            "type": "10Y",
            "yield": "16.801",
            "price_change_day": "0.0490",
            "percentage_week": "-0.05%",
            "percentage_month": "-0.21%",
            "percentage_year": "0.57%",
            "date": "2024-11-08"
        }
    ]
}

```


**API Response Objects:**

**Scroll left & right to navigate**


|Response Object    |Description                                                 |
|-------------------|------------------------------------------------------------|
|pagination > limit |Returns your pagination limit value.                        |
|pagination > offset|Returns your pagination offset value.                       |
|pagination > count |Returns the results count on the current page.              |
|pagination > total |Returns the total count of results available.               |
|region             |Returns the region where the bond is supported.             |
|country            |Returns the country where the bond is supported.            |
|type               |Returns the type of the bond.                               |
|yield              |Returns the current bond yield.                             |
|price_change_day   |Returns the price change of a bond in a day.                |
|percentage_week    |Returns the price change of a bond in a week in percentage. |
|percentage_month   |Returns the price change of a bond in a month in percentage.|
|percentage_year    |Returns the price change of a bond in a year in percentage. |
|date               |Returns the current date info.                              |


  

### ETF Holdings Listing Available on: Basic Plan and higher

The ETF Holdings API delivers instantly complete set of exchange-traded funds data based on the unique identifier code of an ETF data. API End points return the full list of supported ETF tickers.

The example API request below illustrates how to obtain data for the ETF Holdings.

**Note:** The ETF API endpoints have a CALL COUNT MULTIPLIER of 20.

**Example API Request:**

```

Sign Up to Run API Requesthttps://api.marketstack.com/v2/etflist
    ? access_key = YOUR_ACCESS_KEY
    & list = ticker

```


**Endpoint Features:**

**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: list
  * Description: [Required] Specify your list as ticker for your request.
* Object: limit
  * Description: [Optional] Specify a pagination limit (number of results per page) for your API request. Default limit value is 100, maximum allowed limit value is 1000.
* Object: offset
  * Description: [Optional] Specify a pagination offset value for your API request. Example: An offset value of 100 combined with a limit value of 10 would show results 100-110. Default value is 0, starting with the first available result. 


**API Response:**

```
{
    "pagination": {
        "limit": 100,
        "offset": 0,
        "count": 100,
        "total": 1104
    },
    "data": [
        {
            "ticker": "PIFFX"
        },
        {
            "ticker": "PIG.PA"
        },
        {
            "ticker": "PIGDX"
        },
        [...]
    ]
}

```


**API Response Objects:**

**Scroll left & right to navigate**


|Response Object    |Description                                                     |
|-------------------|----------------------------------------------------------------|
|pagination > limit |Returns your pagination limit value.                            |
|pagination > offset|Returns your pagination offset value.                           |
|pagination > count |Returns the results count on the current page.                  |
|pagination > total |Returns the total count of results available.                   |
|ticker             |A unique symbol assigned to publicly traded shares of a company.|


  

### ETF Holdings Info Available on: Basic Plan and higher

The ETF Holdings API delivers instantly complete set of exchange-traded funds data based on the unique identifier code of an ETF data Informaion. API End points return the details for the desired ETF ticker.

The example API request below illustrates how to obtain data for the Stock market index Information.

**Note:** The ETF API endpoints have a CALL COUNT MULTIPLIER of 20.

**Example API Request:**

```

Sign Up to Run API Requesthttps://api.marketstack.com/v2/etfholdings
    ? access_key = YOUR_ACCESS_KEY
    & ticker = PIFFX

```


**Endpoint Features:**

**HTTPS GET Request Parameters:**

**Scroll left & right to navigate**



* Object: access_key
  * Description: [Required] Specify your API access key, available in your account dashboard.
* Object: ticker
  * Description: [Required] To get results based on a ETF ticker.
* Object: date_from
  * Description: [Optional] Filter results based on a specific timeframe by passing a from-date in YYYY-MM-DD format.
* Object: date_to
  * Description: [Optional] Filter results based on a specific timeframe by passing an end-date in YYYY-MM-DD format.


**API Response:**

```
{
    "basics": {
        "fund_name": "AIM Investment Funds (Invesco Investment Funds)",
        "file_number": "811-05426",
        "cik": "0000826644",
        "reg_lei": "Y5W0BJB7U2X9V6NIC803"
    },
    "output": {
        "attributes": {
            "series_name": "Invesco Multi-Asset Income Fund",
            "series_id": "S000035024",
            "series_lei": "54930019G62M8SP8B305",
            "ticker": "PIFFX",
            "isin": "US00888Y8396",
            "date_report_period": "2024-04-30",
            "end_report_period": "2024-10-31",
            "final_filing": false
        },
        "signature": {
            "date_signed": "2024-05-30",
            "name_of_applicant": "AIM Investment Funds (Invesco Investment Funds)",
            "signature": "Adrien Deberghes",
            "signer_name": "Adrien Deberghes",
            "title": "Principal Financial Officer and Treasurer"
        },
        "holdings": [
            {
                "investment_security": {
                    "lei": "549300MHDRBVRF6B9117",
                    "isin": "US195325DL65",
                    "name": "Colombia Government International Bond",
                    "cusip": "195325DL6",
                    "title": "Colombia Government International Bond",
                    "units": "PA",
                    "balance": "2250000.00000000",
                    "currency": "USD",
                    "value_usd": "2093614.81000000",
                    "loan_by_fund": "N",
                    "percent_value": "0.208307501168",
                    "asset_category": "DBT",
                    "payoff_profile": "Long",
                    "restricted_sec": "N",
                    "cash_collateral": "N",
                    "issuer_category": "NUSS",
                    "fair_value_level": "2",
                    "invested_country": "CO",
                    "non_cash_collateral": "N"
                }
            },
            [...]
        ]
    }
}

```


**API Response Objects:**

**Scroll left & right to navigate**



* Response Object: fund_name
  * Description: Returns the information for the Fund Name
* Response Object: file_number
  * Description: Returns the file number under which the fund is registered.
* Response Object: cik
  * Description: Returns the. SEC assigned key of the main trust fund
* Response Object: reg_lei
  * Description: Returns the legal Entity Identifier.
* Response Object: output > attributes > series_name
  * Description: Returns the name of the ETF series held by the fund.
* Response Object: output > attributes > series_id
  * Description: Returns the ID of the ETF held by the fund.
* Response Object: output > attributes > series_lei
  * Description: Returns the legal Entity Identifier of the ETF held by the fund.
* Response Object: output > attributes > ticker
  * Description: Returns the unique ticker symbol assigned to the ETF.
* Response Object: output > attributes > isin
  * Description: Returns international Securities Identification Number.
* Response Object: output > attributes > date_report_period
  * Description: Returns the start date of the report needed.
* Response Object: output > attributes > end_report_period
  * Description: Returns the end date of the report needed.
* Response Object: output > attributes > final_filing
  * Description: Returns the final filling number.
* Response Object: output > signature > date_signed
  * Description: Returns the date when the report is signed.
* Response Object: output > signature > name_of_applicant
  * Description: Returns the name information of the applicant.
* Response Object: output > signature > signature
  * Description: Returns the signature of the person who signed the report.
* Response Object: output > signature > signer_name
  * Description: Returns the name of the person who signed the report.
* Response Object: output > signature > title
  * Description: Returns the title of the person who signed the report.
* Response Object: output > holdings > investment_security > lei
  * Description: Returns the legal Entity Identifier.
* Response Object: output > holdings > investment_security > isin
  * Description: Returns international Securities Identification Number.
* Response Object: output > holdings > investment_security > name
  * Description: Returns the name of the Holding owning the ETF.
* Response Object: output > holdings > investment_security > cusip
  * Description: Returns nine-digit standard for identifying securities, only used for securities issued in the United States and Canada.
* Response Object: output > holdings > investment_security > title
  * Description: Returns the title of the holding.
* Response Object: output > holdings > investment_security > units
  * Description: Returns the units.
* Response Object: output > holdings > investment_security > balance
  * Description: Returns the holding balance.
* Response Object: output > holdings > investment_security > currency
  * Description: Returns the currency.
* Response Object: output > holdings > investment_security > value_usd
  * Description: Returns the value usd.
* Response Object: output > holdings > investment_security > loan_by_fund
  * Description: Returns the loan by fund.
* Response Object: output > holdings > investment_security > percent_value
  * Description: Returns the percent value.
* Response Object: output > holdings > investment_security > asset_category
  * Description: Returns the asset category.
* Response Object: output > holdings > investment_security > payoff_profile
  * Description: Returns the payoff profile.
* Response Object: output > holdings > investment_security > restricted_sec
  * Description: Returns the restricted sec.
* Response Object: output > holdings > investment_security > cash_collateral
  * Description: Returns the cash collateral.
* Response Object: output > holdings > investment_security > issuer_category
  * Description: Returns the issuer category.
* Response Object: output > holdings > investment_security > fair_value_level
  * Description: Returns the fair value level.
* Response Object: output > holdings > investment_security > invested_country
  * Description: Returns the invested country.
* Response Object: output > holdings > investment_security > non_cash_collateral
  * Description: Returns the non cash collateral.


  

### ETF Holding Info (timeframe) Available on: Basic Plan and higher

ETF Holding Info (timeframe) holding data within a specified date range using a unique ticker identifier. You can adjust the ticker, date\_from, and date\_to parameters based on your specific needs.

The example API request below illustrates how to obtain data for the Stock market index Information within a specified date range.

**Note:** The ETF API endpoints have a CALL COUNT MULTIPLIER of 20.

**Example API Request:**

```
Sign Up to Run API Requesthttps://api.marketstack.com/v2/etfholdings
    ? access_key = YOUR_ACCESS_KEY
    & ticker = PIFFX
    & date_from = 2024-04-29
    & date_to = 2024-11-01

```


**HTTPS GET Request Parameters:**

For details on request parameters on the `etfholdings` data endpoint, please jump to the ETF Holdings Information Data section.

**Example API Response:**

```
{
    "basics": {
        "fund_name": "AIM Investment Funds (Invesco Investment Funds)",
        "file_number": "811-05426",
        "cik": "0000826644",
        "reg_lei": "Y5W0BJB7U2X9V6NIC803"
    },
    "output": {
        "attributes": {
            "series_name": "Invesco Multi-Asset Income Fund",
            "series_id": "S000035024",
            "series_lei": "54930019G62M8SP8B305",
            "ticker": "PIFFX",
            "isin": "US00888Y8396",
            "date_report_period": "2024-04-30",
            "end_report_period": "2024-10-31",
            "final_filing": false
        },
        "signature": {
            "date_signed": "2024-05-30",
            "name_of_applicant": "AIM Investment Funds (Invesco Investment Funds)",
            "signature": "Adrien Deberghes",
            "signer_name": "Adrien Deberghes",
            "title": "Principal Financial Officer and Treasurer"
        },
        "holdings": [
            {
                "investment_security": {
                    "lei": "549300MHDRBVRF6B9117",
                    "isin": "US195325DL65",
                    "name": "Colombia Government International Bond",
                    "cusip": "195325DL6",
                    "title": "Colombia Government International Bond",
                    "units": "PA",
                    "balance": "2250000.00000000",
                    "currency": "USD",
                    "value_usd": "2093614.81000000",
                    "loan_by_fund": "N",
                    "percent_value": "0.208307501168",
                    "asset_category": "DBT",
                    "payoff_profile": "Long",
                    "restricted_sec": "N",
                    "cash_collateral": "N",
                    "issuer_category": "NUSS",
                    "fair_value_level": "2",
                    "invested_country": "CO",
                    "non_cash_collateral": "N"
                }
            },
            [...]
        ]
    }
}

```


**API Response Objects:**

For details of API response objects on the `etfholdings` data endpoint, please jump to the ETF Holdings Information Data section.
