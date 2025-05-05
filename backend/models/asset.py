# models/asset.py

from sqlalchemy import Column, String, Enum as SQLEnum, Numeric, Date, ForeignKey, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

# Make sure to import Base, BaseModel, and your Enums correctly
from backend.core.database import Base # Assuming Base is defined in core.database
from .base_model import IdMixin, TimestampMixin, TableNameMixin
from .enums import AssetType, OptionType, Currency

class Asset(IdMixin, TimestampMixin, TableNameMixin, Base):
    __tablename__ = 'assets' # Explicit table name

    asset_type = Column(SQLEnum(AssetType, name="asset_type_enum", create_type=True, native_enums=True), nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True) # Stock Ticker or Option underlying Ticker
    name = Column(String, nullable=True) # Stock/Company Name or Option description
    currency = Column(SQLEnum(Currency, name="currency_enum", create_type=True, native_enums=True), nullable=False, default=Currency.USD) # Assuming USD default

    # Option-specific fields (nullable)
    option_type = Column(SQLEnum(OptionType, name="option_type_enum", create_type=True, native_enums=True), nullable=True)
    strike_price = Column(Numeric(12, 4), nullable=True)
    expiration_date = Column(Date, nullable=True)
    underlying_asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id'), nullable=True) # Link option to underlying stock asset

    # Relationships
    underlying_asset = relationship("Asset", foreign_keys=[underlying_asset_id], lazy="joined") # Consider lazy loading strategy
    positions = relationship("Position", back_populates="asset")
    transactions = relationship("Transaction", back_populates="asset")

    # Define Table Arguments for Indexes/Constraints
    __table_args__ = (
        # Unique constraint for Stock/ETF symbols:
        # Ensures only one 'Stock' type asset exists per symbol.
        Index(
            'uq_asset_stock_symbol',    # A descriptive name for the index
            symbol,                     # The column(s) this index applies to
            unique=True,                # Makes it a unique index
            postgresql_where=text(f"asset_type = '{AssetType.STOCK.name}'::asset_type_enum") # The partial index condition
        ),

        # Unique constraint for Option contracts:
        # Ensures only one option asset exists for a given underlying, type, strike, and expiration.
        Index(
            'uq_asset_option_contract', # A descriptive name for the index
            underlying_asset_id,        # Column combination for uniqueness
            option_type,
            strike_price,
            expiration_date,
            unique=True,                # Makes it a unique index
            postgresql_where=text(f"asset_type = '{AssetType.OPTION.name}'::asset_type_enum") # The partial index condition
        ),

        # Add other table args like schema settings here if needed, e.g.:
        # {'schema': 'my_schema'}
    )
    print("--Loading UPDATED models/asset.py --")

    def __repr__(self):
        if self.asset_type == AssetType.STOCK:
            return f"<Asset(type='{self.asset_type.value}', symbol='{self.symbol}')>"
        elif self.asset_type == AssetType.OPTION:
            return (f"<Asset(type='{self.asset_type.value}', "
                    f"underlying='{self.symbol}', strike={self.strike_price}, "
                    f"expiry='{self.expiration_date}', option_type='{self.option_type.value}')>")
        else:
            return f"<Asset(id='{self.id}', type='{self.asset_type.value}')>"