# backend/tests/services/test_market_data_service.py
import pytest
from datetime import datetime, timedelta, date
from unittest.mock import AsyncMock, patch

from backend.services.market_data_service import MarketDataService
from backend.schemas.market_data import (
    IntradayPricePoint, 
    RealtimeStockPrice, 
    StockExchangeInfo, 
    TickerBasicInfo, 
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

@pytest.fixture
def mock_marketstack_adapter():
    """Create a mock MarketStack adapter for testing."""
    adapter = AsyncMock()
    return adapter

@pytest.mark.asyncio
async def test_get_intraday_price_data(mock_marketstack_adapter):
    """Test the get_intraday_price_data method."""
    # Setup mock response
    mock_data = [
        IntradayPricePoint(
            symbol="AAPL",
            date=datetime.now(),
            open=150.0,
            high=152.0,
            low=149.0,
            close=151.0,
            last=151.0,
            volume=1000000
        )
    ]
    mock_marketstack_adapter.get_intraday_price_data.return_value = mock_data
    
    # Create service with mock adapter
    with patch('backend.services.market_data_service.MarketStackAdapter', return_value=mock_marketstack_adapter):
        service = MarketDataService()
        
        # Call the method
        result = await service.get_intraday_price_data(
            symbol="AAPL",
            interval="1hour",
            from_date=datetime.now() - timedelta(days=1),
            to_date=datetime.now()
        )
        
        # Verify the result
        assert result == mock_data
        assert len(result) == 1
        assert result[0].symbol == "AAPL"
        assert result[0].open == 150.0
        
        # Verify the adapter was called with correct parameters
        mock_marketstack_adapter.get_intraday_price_data.assert_called_once()
        call_args = mock_marketstack_adapter.get_intraday_price_data.call_args[0]
        assert call_args[0] == "AAPL"  # symbol
        assert call_args[1] == "1hour"  # interval

@pytest.mark.asyncio
async def test_get_realtime_stock_price(mock_marketstack_adapter):
    """Test the get_realtime_stock_price method."""
    # Setup mock response
    mock_data = [
        RealtimeStockPrice(
            exchange_code="XNAS",
            exchange_name="NASDAQ Stock Exchange",
            country="United States of America",
            ticker="AAPL",
            price=150.0,
            currency="USD",
            trade_last=datetime.now()
        )
    ]
    mock_marketstack_adapter.get_realtime_stock_price.return_value = mock_data
    
    # Create service with mock adapter
    with patch('backend.services.market_data_service.MarketStackAdapter', return_value=mock_marketstack_adapter):
        service = MarketDataService()
        
        # Call the method
        result = await service.get_realtime_stock_price(ticker="AAPL")
        
        # Verify the result
        assert result == mock_data
        assert len(result) == 1
        assert result[0].ticker == "AAPL"
        assert result[0].exchange_code == "XNAS"
        
        # Verify the adapter was called with correct parameters
        mock_marketstack_adapter.get_realtime_stock_price.assert_called_once_with("AAPL", None)

@pytest.mark.asyncio
async def test_list_exchanges(mock_marketstack_adapter):
    """Test the list_exchanges method."""
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
    mock_marketstack_adapter.list_exchanges.return_value = mock_data
    
    # Create service with mock adapter
    with patch('backend.services.market_data_service.MarketStackAdapter', return_value=mock_marketstack_adapter):
        service = MarketDataService()
        
        # Call the method
        result = await service.list_exchanges()
        
        # Verify the result
        assert result == mock_data
        assert len(result) == 1
        assert result[0].mic == "XNAS"
        
        # Verify the adapter was called with correct parameters
        mock_marketstack_adapter.list_exchanges.assert_called_once_with(None, 100, 0)

# Phase 2 - Commodity Prices
@pytest.mark.asyncio
async def test_get_commodity_price(mock_marketstack_adapter):
    """Test the get_commodity_price method."""
    # Setup mock response
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
        datetime=datetime.now()
    )
    mock_marketstack_adapter.get_commodity_price.return_value = mock_data
    
    # Create service with mock adapter
    with patch('backend.services.market_data_service.MarketStackAdapter', return_value=mock_marketstack_adapter):
        service = MarketDataService()
        
        # Call the method
        result = await service.get_commodity_price(commodity_name="gold")
        
        # Verify the result
        assert result == mock_data
        assert result.commodity_name == "gold"
        assert result.commodity_unit == "troy ounce"
        assert result.commodity_price == 1982.45
        
        # Verify the adapter was called with correct parameters
        mock_marketstack_adapter.get_commodity_price.assert_called_once_with("gold")

# Phase 2 - Historical Commodity Prices
@pytest.mark.asyncio
async def test_get_historical_commodity_prices(mock_marketstack_adapter):
    """Test the get_historical_commodity_prices method."""
    # Setup mock response
    mock_data = HistoricalCommodityPriceData(
        basics=CommodityBasics(
            commodity_name="gold",
            commodity_unit="troy ounce"
        ),
        data=[
            CommodityPricePoint(
                commodity_price=1982.45,
                date=datetime.now()
            ),
            CommodityPricePoint(
                commodity_price=1970.12,
                date=datetime.now() - timedelta(days=1)
            )
        ]
    )
    mock_marketstack_adapter.get_historical_commodity_prices.return_value = mock_data
    
    # Create service with mock adapter
    with patch('backend.services.market_data_service.MarketStackAdapter', return_value=mock_marketstack_adapter):
        service = MarketDataService()
        
        # Call the method
        from_date = date.today() - timedelta(days=30)
        to_date = date.today()
        result = await service.get_historical_commodity_prices(
            commodity_name="gold",
            date_from=from_date,
            date_to=to_date,
            frequency="daily"
        )
        
        # Verify the result
        assert result == mock_data
        assert result.basics.commodity_name == "gold"
        assert len(result.data) == 2
        assert result.data[0].commodity_price == 1982.45
        
        # Verify the adapter was called with correct parameters
        mock_marketstack_adapter.get_historical_commodity_prices.assert_called_once_with(
            "gold", from_date, to_date, "daily"
        )

# Phase 2 - Company Ratings
@pytest.mark.asyncio
async def test_get_company_ratings(mock_marketstack_adapter):
    """Test the get_company_ratings method."""
    # Setup mock response
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
                        rating_date=datetime.now() - timedelta(days=15)
                    ),
                    AnalystRatingDetail(
                        analyst_name="Goldman Sachs",
                        analyst_rating="buy",
                        target_price=190.00,
                        rating_date=datetime.now() - timedelta(days=20)
                    )
                ]
            )
        )
    )
    mock_marketstack_adapter.get_company_ratings.return_value = mock_data
    
    # Create service with mock adapter
    with patch('backend.services.market_data_service.MarketStackAdapter', return_value=mock_marketstack_adapter):
        service = MarketDataService()
        
        # Call the method
        from_date = date.today() - timedelta(days=30)
        to_date = date.today()
        result = await service.get_company_ratings(
            ticker="AAPL",
            date_from=from_date,
            date_to=to_date,
            rated="buy"
        )
        
        # Verify the result
        assert result == mock_data
        assert result.result.basics.ticker == "AAPL"
        assert result.result.output.analyst_consensus.buy == 25
        assert len(result.result.output.analysts) == 2
        
        # Verify the adapter was called with correct parameters
        mock_marketstack_adapter.get_company_ratings.assert_called_once_with(
            "AAPL", from_date, to_date, "buy"
        )

# Phase 2 - Stock Market Index Listing
@pytest.mark.asyncio
async def test_list_stock_market_indexes(mock_marketstack_adapter):
    """Test the list_stock_market_indexes method."""
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
    mock_marketstack_adapter.list_stock_market_indexes.return_value = mock_data
    
    # Create service with mock adapter
    with patch('backend.services.market_data_service.MarketStackAdapter', return_value=mock_marketstack_adapter):
        service = MarketDataService()
        
        # Call the method
        result = await service.list_stock_market_indexes(limit=100, offset=0)
        
        # Verify the result
        assert result == mock_data
        assert len(result) == 2
        assert result[0].benchmark == "SPX"
        assert result[1].benchmark == "DJI"
        
        # Verify the adapter was called with correct parameters
        mock_marketstack_adapter.list_stock_market_indexes.assert_called_once_with(100, 0)

# Phase 2 - Bonds Data
@pytest.mark.asyncio
async def test_list_bond_countries(mock_marketstack_adapter):
    """Test the list_bond_countries method."""
    # Setup mock response
    mock_data = [
        BondCountry(country="United States"),
        BondCountry(country="Germany"),
        BondCountry(country="Japan")
    ]
    mock_marketstack_adapter.list_bond_countries.return_value = mock_data
    
    # Create service with mock adapter
    with patch('backend.services.market_data_service.MarketStackAdapter', return_value=mock_marketstack_adapter):
        service = MarketDataService()
        
        # Call the method
        result = await service.list_bond_countries(limit=100, offset=0)
        
        # Verify the result
        assert result == mock_data
        assert len(result) == 3
        assert result[0].country == "United States"
        
        # Verify the adapter was called with correct parameters
        mock_marketstack_adapter.list_bond_countries.assert_called_once_with(100, 0)

@pytest.mark.asyncio
async def test_get_bond_info(mock_marketstack_adapter):
    """Test the get_bond_info method."""
    # Setup mock response
    mock_data = BondInfoData(
        region="North America",
        country="United States",
        type="10-Year",
        yield_value=3.45,
        price_change_day=0.05,
        percentage_week=1.25,
        percentage_month=2.78,
        percentage_year=8.45,
        datetime=datetime.now()
    )
    mock_marketstack_adapter.get_bond_info.return_value = mock_data
    
    # Create service with mock adapter
    with patch('backend.services.market_data_service.MarketStackAdapter', return_value=mock_marketstack_adapter):
        service = MarketDataService()
        
        # Call the method
        result = await service.get_bond_info(country="United States")
        
        # Verify the result
        assert result == mock_data
        assert result.country == "United States"
        assert result.type == "10-Year"
        assert result.yield_value == 3.45
        
        # Verify the adapter was called with correct parameters
        mock_marketstack_adapter.get_bond_info.assert_called_once_with("United States")

# Phase 2 - ETF Data
@pytest.mark.asyncio
async def test_list_etfs(mock_marketstack_adapter):
    """Test the list_etfs method."""
    # Setup mock response
    mock_data = [
        ETFTicker(ticker="SPY"),
        ETFTicker(ticker="QQQ"),
        ETFTicker(ticker="VTI")
    ]
    mock_marketstack_adapter.list_etfs.return_value = mock_data
    
    # Create service with mock adapter
    with patch('backend.services.market_data_service.MarketStackAdapter', return_value=mock_marketstack_adapter):
        service = MarketDataService()
        
        # Call the method
        result = await service.list_etfs(limit=100, offset=0)
        
        # Verify the result
        assert result == mock_data
        assert len(result) == 3
        assert result[0].ticker == "SPY"
        
        # Verify the adapter was called with correct parameters
        mock_marketstack_adapter.list_etfs.assert_called_once_with(100, 0)

@pytest.mark.asyncio
async def test_get_etf_holdings(mock_marketstack_adapter):
    """Test the get_etf_holdings method."""
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
    mock_marketstack_adapter.get_etf_holdings.return_value = mock_data
    
    # Create service with mock adapter
    with patch('backend.services.market_data_service.MarketStackAdapter', return_value=mock_marketstack_adapter):
        service = MarketDataService()
        
        # Call the method
        from_date = date.today() - timedelta(days=30)
        to_date = date.today()
        result = await service.get_etf_holdings(
            ticker="SPY",
            date_from=from_date,
            date_to=to_date
        )
        
        # Verify the result
        assert result == mock_data
        assert result.basics.ticker == "SPY"
        assert result.output.attributes.aum == 373500000000
        assert len(result.output.signature.sector_weights) == 3
        assert len(result.output.holdings) == 2
        assert result.output.holdings[0].ticker == "AAPL"
        
        # Verify the adapter was called with correct parameters
        mock_marketstack_adapter.get_etf_holdings.assert_called_once_with(
            "SPY", from_date, to_date
        )