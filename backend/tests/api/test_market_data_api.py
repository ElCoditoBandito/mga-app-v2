# backend/tests/api/test_market_data_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta, date

from backend.main import app
from backend.services.market_data_service import MarketDataService
from backend.schemas.market_data import (
    IntradayPricePoint, 
    RealtimeStockPrice, 
    StockExchangeInfo, 
    CurrencyInfo, 
    TimezoneInfo,
    # Phase 2 additions
    CommodityPrice,
    HistoricalCommodityPriceData,
    CommodityBasics,
    CommodityPricePoint,
    CompanyRatingData,
    CompanyRatingResult,
    CompanyBasics,
    CompanyRatingOutput,
    AnalystConsensus,
    AnalystRatingDetail,
    IndexBasicInfo,
    BondCountry,
    BondInfoData,
    ETFTicker,
    ETFHoldingDetails,
    ETFBasics,
    ETFOutput,
    ETFAttributes,
    ETFSignature,
    SectorWeight,
    ETFHolding
)

# Create a test client
client = TestClient(app)

@pytest.fixture
def mock_market_data_service():
    """Create a mock MarketDataService for testing."""
    service = AsyncMock()
    return service

def test_read_intraday_price_data(mock_market_data_service):
    """Test the /market-data/intraday/{symbol} endpoint."""
    # Setup mock response
    now = datetime.now()
    mock_data = [
        IntradayPricePoint(
            symbol="AAPL",
            date=now,
            open=150.0,
            high=152.0,
            low=149.0,
            close=151.0,
            last=151.0,
            volume=1000000
        )
    ]
    mock_market_data_service.get_intraday_price_data.return_value = mock_data
    
    # Mock the dependency
    app.dependency_overrides[MarketDataService] = lambda: mock_market_data_service
    
    # Make the request
    response = client.get("/api/v1/market-data/intraday/AAPL?interval=1hour")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"
    assert data[0]["open"] == 150.0
    
    # Verify the service was called with correct parameters
    mock_market_data_service.get_intraday_price_data.assert_called_once()
    
    # Clean up
    app.dependency_overrides = {}

def test_read_realtime_stock_price(mock_market_data_service):
    """Test the /market-data/realtime/{ticker} endpoint."""
    # Setup mock response
    now = datetime.now()
    mock_data = [
        RealtimeStockPrice(
            exchange_code="XNAS",
            exchange_name="NASDAQ Stock Exchange",
            country="United States of America",
            ticker="AAPL",
            price=150.0,
            currency="USD",
            trade_last=now
        )
    ]
    mock_market_data_service.get_realtime_stock_price.return_value = mock_data
    
    # Mock the dependency
    app.dependency_overrides[MarketDataService] = lambda: mock_market_data_service
    
    # Make the request
    response = client.get("/api/v1/market-data/realtime/AAPL")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["ticker"] == "AAPL"
    assert data[0]["exchange_code"] == "XNAS"
    assert data[0]["price"] == 150.0
    
    # Verify the service was called with correct parameters
    mock_market_data_service.get_realtime_stock_price.assert_called_once_with("AAPL", None)
    
    # Clean up
    app.dependency_overrides = {}

def test_list_exchanges(mock_market_data_service):
    """Test the /market-data/exchanges endpoint."""
    # Setup mock response
    mock_data = [
        StockExchangeInfo(
            name="NASDAQ Stock Exchange",
            acronym="NASDAQ",
            mic="XNAS",
            country="United States of America",
            country_code="US",
            city="New York",
            website="www.nasdaq.com"
        )
    ]
    mock_market_data_service.list_exchanges.return_value = mock_data
    
    # Mock the dependency
    app.dependency_overrides[MarketDataService] = lambda: mock_market_data_service
    
    # Make the request
    response = client.get("/api/v1/market-data/exchanges")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "NASDAQ Stock Exchange"
    assert data[0]["mic"] == "XNAS"
    
    # Verify the service was called with correct parameters
    mock_market_data_service.list_exchanges.assert_called_once()
    
    # Clean up
    app.dependency_overrides = {}

def test_get_exchange_details(mock_market_data_service):
    """Test the /market-data/exchanges/{mic} endpoint."""
    # Setup mock response
    mock_data = StockExchangeInfo(
        name="NASDAQ Stock Exchange",
        acronym="NASDAQ",
        mic="XNAS",
        country="United States of America",
        country_code="US",
        city="New York",
        website="www.nasdaq.com"
    )
    mock_market_data_service.get_exchange_details.return_value = mock_data
    
    # Mock the dependency
    app.dependency_overrides[MarketDataService] = lambda: mock_market_data_service
    
    # Make the request
    response = client.get("/api/v1/market-data/exchanges/XNAS")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "NASDAQ Stock Exchange"
    assert data["mic"] == "XNAS"
    
    # Verify the service was called with correct parameters
    mock_market_data_service.get_exchange_details.assert_called_once_with("XNAS")
    
    # Clean up
    app.dependency_overrides = {}

def test_list_currencies(mock_market_data_service):
    """Test the /market-data/currencies endpoint."""
    # Setup mock response
    mock_data = [
        CurrencyInfo(
            code="USD",
            name="US Dollar",
            symbol="$",
            symbol_native="$"
        )
    ]
    mock_market_data_service.list_currencies.return_value = mock_data
    
    # Mock the dependency
    app.dependency_overrides[MarketDataService] = lambda: mock_market_data_service
    
    # Make the request
    response = client.get("/api/v1/market-data/currencies")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["code"] == "USD"
    assert data[0]["name"] == "US Dollar"
    
    # Verify the service was called with correct parameters
    mock_market_data_service.list_currencies.assert_called_once()
    
    # Clean up
    app.dependency_overrides = {}

def test_list_timezones(mock_market_data_service):
    """Test the /market-data/timezones endpoint."""
    # Setup mock response
    mock_data = [
        TimezoneInfo(
            timezone="America/New_York",
            abbr="EDT",
            abbr_dst="EDT"
        )
    ]
    mock_market_data_service.list_timezones.return_value = mock_data
    
    # Mock the dependency
    app.dependency_overrides[MarketDataService] = lambda: mock_market_data_service
    
    # Make the request
    response = client.get("/api/v1/market-data/timezones")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["timezone"] == "America/New_York"
    assert data[0]["abbr"] == "EDT"
    
    # Verify the service was called with correct parameters
    mock_market_data_service.list_timezones.assert_called_once()
    
    # Clean up
    app.dependency_overrides = {}

# Phase 2 - Commodity Prices
def test_get_commodity_price(mock_market_data_service):
    """Test the /market-data/commodities/{commodity_name} endpoint."""
    # Setup mock response
    now = datetime.now()
    mock_data = CommodityPrice(
        commodity_name="gold",
        commodity_unit="troy ounce",
        commodity_price=1982.45,
        price_change_day=12.34,
        percentage_day=0.63,
        percentage_week=1.25,
        percentage_month=2.78,
        percentage_year=8.45,
        quarter1_25=1850.23,
        quarter2_25=1875.67,
        quarter3_25=1920.12,
        quarter4_25=1950.89,
        quarter1_24=1820.45,
        quarter2_24=1840.78,
        quarter3_24=1880.34,
        quarter4_24=1910.56,
        quarter1_23=1780.23,
        quarter2_23=1800.45,
        quarter3_23=1830.67,
        quarter4_23=1860.89,
        datetime=now
    )
    mock_market_data_service.get_commodity_price.return_value = mock_data
    
    # Mock the dependency
    app.dependency_overrides[MarketDataService] = lambda: mock_market_data_service
    
    # Make the request
    response = client.get("/api/v1/market-data/commodities/gold")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["commodity_name"] == "gold"
    assert data["data"]["commodity_unit"] == "troy ounce"
    assert data["data"]["commodity_price"] == 1982.45
    
    # Verify the service was called with correct parameters
    mock_market_data_service.get_commodity_price.assert_called_once_with("gold")
    
    # Clean up
    app.dependency_overrides = {}

# Phase 2 - Historical Commodity Prices
def test_get_historical_commodity_prices(mock_market_data_service):
    """Test the /market-data/commodities/{commodity_name}/historical endpoint."""
    # Setup mock response
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    mock_data = HistoricalCommodityPriceData(
        basics=CommodityBasics(
            commodity_name="gold",
            commodity_unit="troy ounce"
        ),
        data=[
            CommodityPricePoint(
                commodity_price=1982.45,
                date=now
            ),
            CommodityPricePoint(
                commodity_price=1970.12,
                date=yesterday
            )
        ]
    )
    mock_market_data_service.get_historical_commodity_prices.return_value = mock_data
    
    # Mock the dependency
    app.dependency_overrides[MarketDataService] = lambda: mock_market_data_service
    
    # Make the request
    from_date = date.today() - timedelta(days=30)
    to_date = date.today()
    response = client.get(f"/api/v1/market-data/commodities/gold/historical?from={from_date}&to={to_date}&frequency=daily")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["basics"]["commodity_name"] == "gold"
    assert len(data["data"]["data"]) == 2
    assert data["data"]["data"][0]["commodity_price"] == 1982.45
    
    # Verify the service was called with correct parameters
    mock_market_data_service.get_historical_commodity_prices.assert_called_once()
    call_args = mock_market_data_service.get_historical_commodity_prices.call_args[0]
    assert call_args[0] == "gold"  # commodity_name
    
    # Clean up
    app.dependency_overrides = {}

# Phase 2 - Company Ratings
def test_get_company_ratings(mock_market_data_service):
    """Test the /market-data/companies/{ticker}/ratings endpoint."""
    # Setup mock response
    now = datetime.now()
    mock_data = CompanyRatingData(
        status="ok",
        result=CompanyRatingResult(
            basics=CompanyBasics(
                ticker="AAPL",
                name="Apple Inc.",
                exchange="NASDAQ"
            ),
            output=CompanyRatingOutput(
                analyst_consensus=AnalystConsensus(
                    buy=25,
                    hold=8,
                    sell=2,
                    average_rating=1.91,
                    average_target_price=178.45,
                    high_target_price=210.00,
                    low_target_price=150.00,
                    median_target_price=180.00
                ),
                analysts=[
                    AnalystRatingDetail(
                        analyst_name="Morgan Stanley",
                        analyst_rating="buy",
                        target_price=180.00,
                        rating_date=now - timedelta(days=15)
                    ),
                    AnalystRatingDetail(
                        analyst_name="Goldman Sachs",
                        analyst_rating="buy",
                        target_price=190.00,
                        rating_date=now - timedelta(days=20)
                    )
                ]
            )
        )
    )
    mock_market_data_service.get_company_ratings.return_value = mock_data
    
    # Mock the dependency
    app.dependency_overrides[MarketDataService] = lambda: mock_market_data_service
    
    # Make the request
    from_date = date.today() - timedelta(days=30)
    to_date = date.today()
    response = client.get(f"/api/v1/market-data/companies/AAPL/ratings?from={from_date}&to={to_date}&rated=buy")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["result"]["basics"]["ticker"] == "AAPL"
    assert data["data"]["result"]["output"]["analyst_consensus"]["buy"] == 25
    assert len(data["data"]["result"]["output"]["analysts"]) == 2
    
    # Verify the service was called with correct parameters
    mock_market_data_service.get_company_ratings.assert_called_once()
    call_args = mock_market_data_service.get_company_ratings.call_args[0]
    assert call_args[0] == "AAPL"  # ticker
    
    # Clean up
    app.dependency_overrides = {}

# Phase 2 - Stock Market Index Listing
def test_list_stock_market_indexes(mock_market_data_service):
    """Test the /market-data/indices endpoint."""
    # Setup mock response
    mock_data = [
        IndexBasicInfo(
            benchmark="SPX",
            name="S&P 500",
            country="United States",
            currency="USD"
        ),
        IndexBasicInfo(
            benchmark="DJI",
            name="Dow Jones Industrial Average",
            country="United States",
            currency="USD"
        )
    ]
    mock_market_data_service.list_stock_market_indexes.return_value = mock_data
    
    # Mock the dependency
    app.dependency_overrides[MarketDataService] = lambda: mock_market_data_service
    
    # Make the request
    response = client.get("/api/v1/market-data/indices?limit=100&offset=0")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["data"][0]["benchmark"] == "SPX"
    assert data["data"][1]["benchmark"] == "DJI"
    
    # Verify the service was called with correct parameters
    mock_market_data_service.list_stock_market_indexes.assert_called_once_with(100, 0)
    
    # Clean up
    app.dependency_overrides = {}

# Phase 2 - Bonds Data
def test_list_bond_countries(mock_market_data_service):
    """Test the /market-data/bonds endpoint."""
    # Setup mock response
    mock_data = [
        BondCountry(country="United States"),
        BondCountry(country="Germany"),
        BondCountry(country="Japan")
    ]
    mock_market_data_service.list_bond_countries.return_value = mock_data
    
    # Mock the dependency
    app.dependency_overrides[MarketDataService] = lambda: mock_market_data_service
    
    # Make the request
    response = client.get("/api/v1/market-data/bonds?limit=100&offset=0")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 3
    assert data["data"][0]["country"] == "United States"
    
    # Verify the service was called with correct parameters
    mock_market_data_service.list_bond_countries.assert_called_once_with(100, 0)
    
    # Clean up
    app.dependency_overrides = {}

def test_get_bond_info(mock_market_data_service):
    """Test the /market-data/bonds/{country} endpoint."""
    # Setup mock response
    now = datetime.now()
    mock_data = BondInfoData(
        region="North America",
        country="United States",
        type="10-Year",
        yield_value=3.45,
        price_change_day=0.05,
        percentage_week=1.25,
        percentage_month=2.78,
        percentage_year=8.45,
        datetime=now
    )
    mock_market_data_service.get_bond_info.return_value = mock_data
    
    # Mock the dependency
    app.dependency_overrides[MarketDataService] = lambda: mock_market_data_service
    
    # Make the request
    response = client.get("/api/v1/market-data/bonds/United%20States")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["country"] == "United States"
    assert data["data"]["type"] == "10-Year"
    assert data["data"]["yield_value"] == 3.45
    
    # Verify the service was called with correct parameters
    mock_market_data_service.get_bond_info.assert_called_once_with("United States")
    
    # Clean up
    app.dependency_overrides = {}

# Phase 2 - ETF Data
def test_list_etfs(mock_market_data_service):
    """Test the /market-data/etfs endpoint."""
    # Setup mock response
    mock_data = [
        ETFTicker(ticker="SPY"),
        ETFTicker(ticker="QQQ"),
        ETFTicker(ticker="VTI")
    ]
    mock_market_data_service.list_etfs.return_value = mock_data
    
    # Mock the dependency
    app.dependency_overrides[MarketDataService] = lambda: mock_market_data_service
    
    # Make the request
    response = client.get("/api/v1/market-data/etfs?limit=100&offset=0")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 3
    assert data["data"][0]["ticker"] == "SPY"
    
    # Verify the service was called with correct parameters
    mock_market_data_service.list_etfs.assert_called_once_with(100, 0)
    
    # Clean up
    app.dependency_overrides = {}

def test_get_etf_holdings(mock_market_data_service):
    """Test the /market-data/etfs/{ticker}/holdings endpoint."""
    # Setup mock response
    mock_data = ETFHoldingDetails(
        basics=ETFBasics(
            ticker="SPY",
            name="SPDR S&P 500 ETF Trust",
            exchange="NYSE Arca"
        ),
        output=ETFOutput(
            attributes=ETFAttributes(
                aum=373500000000,
                expense_ratio=0.0945,
                shares_outstanding=934500000,
                nav=400.12
            ),
            signature=ETFSignature(
                sector_weights=[
                    SectorWeight(sector="Information Technology", weight=26.8),
                    SectorWeight(sector="Health Care", weight=14.2),
                    SectorWeight(sector="Financials", weight=13.1)
                ]
            ),
            holdings=[
                ETFHolding(
                    ticker="AAPL",
                    name="Apple Inc.",
                    weight=7.12,
                    shares=6250000,
                    market_value=26500000000
                ),
                ETFHolding(
                    ticker="MSFT",
                    name="Microsoft Corporation",
                    weight=6.89,
                    shares=5800000,
                    market_value=25700000000
                )
            ]
        )
    )
    mock_market_data_service.get_etf_holdings.return_value = mock_data
    
    # Mock the dependency
    app.dependency_overrides[MarketDataService] = lambda: mock_market_data_service
    
    # Make the request
    from_date = date.today() - timedelta(days=30)
    to_date = date.today()
    response = client.get(f"/api/v1/market-data/etfs/SPY/holdings?from={from_date}&to={to_date}")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["basics"]["ticker"] == "SPY"
    assert data["data"]["output"]["attributes"]["aum"] == 373500000000
    assert len(data["data"]["output"]["signature"]["sector_weights"]) == 3
    assert len(data["data"]["output"]["holdings"]) == 2
    assert data["data"]["output"]["holdings"][0]["ticker"] == "AAPL"
    
    # Verify the service was called with correct parameters
    mock_market_data_service.get_etf_holdings.assert_called_once()
    call_args = mock_market_data_service.get_etf_holdings.call_args[0]
    assert call_args[0] == "SPY"  # ticker
    
    # Clean up
    app.dependency_overrides = {}