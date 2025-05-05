"""
Pydantic Schemas for Asset Resource
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal, Any

from pydantic import BaseModel, Field, model_validator, ConfigDict
from pydantic_core import PydanticCustomError

# Import shared ORM config and enums
from . import orm_config
from backend.models.enums import AssetType, OptionType, Currency

# --- Asset Schemas ---

# Basic Read schema first (can be used by AssetRead)
class AssetReadBasic(BaseModel):
    id: uuid.UUID
    asset_type: AssetType
    symbol: str
    name: Optional[str] = None
    currency: str
    option_type: Optional[OptionType] = None
    strike_price: Optional[Decimal] = Field(None, max_digits=12, decimal_places=4)
    expiration_date: Optional[date] = None
    model_config = orm_config


class AssetBase(BaseModel):
    asset_type: AssetType
    symbol: str = Field(..., example="AAPL") # Stock Ticker or Option Underlying
    name: Optional[str] = Field(None, example="Apple Inc.")
    currency: Currency = Field(default=Currency.USD, min_length=3, max_length=3, example="USD")

    # Option Specific
    option_type: Optional[OptionType] = None
    strike_price: Optional[Decimal] = Field(None, max_digits=12, decimal_places=4, example=Decimal("175.00"))
    expiration_date: Optional[date] = None
    underlying_asset_id: Optional[uuid.UUID] = None

    @model_validator(mode='after')
    def check_option_fields(self) -> 'AssetBase':
        # (Validation logic as defined in previous combined example)
        if self.asset_type == AssetType.OPTION:
            errors = {}
            if self.option_type is None: errors['option_type'] = 'Option type must be set for AssetType.OPTION'
            if self.strike_price is None: errors['strike_price'] = 'Strike price must be set for AssetType.OPTION'
            if self.expiration_date is None: errors['expiration_date'] = 'Expiration date must be set for AssetType.OPTION'
            if self.underlying_asset_id is None: errors['underlying_asset_id'] = 'Underlying asset ID must be set for AssetType.OPTION'
            if errors: raise PydanticCustomError('value_error', "Option validation errors: {errors}", {'errors': errors})
        elif self.asset_type != AssetType.OPTION:
            errors = {}
            if self.option_type is not None: errors['option_type'] = 'Option type must be null for non-Option AssetType'
            if self.strike_price is not None: errors['strike_price'] = 'Strike price must be null for non-Option AssetType'
            if self.expiration_date is not None: errors['expiration_date'] = 'Expiration date must be null for non-Option AssetType'
            if self.underlying_asset_id is not None: errors['underlying_asset_id'] = 'Underlying asset ID must be null for non-Option AssetType'
            if errors: raise PydanticCustomError('value_error', "Non-Option validation errors: {errors}", {'errors': errors})
        return self

# Specific Create Schemas
class AssetCreateStock(BaseModel):
    asset_type: Literal[AssetType.STOCK] = Field(AssetType.STOCK)
    symbol: str = Field(..., example="MSFT")
    name: Optional[str] = Field(None, example="Microsoft Corporation")

class AssetCreateOption(BaseModel):
    asset_type: Literal[AssetType.OPTION] = Field(AssetType.OPTION)
    underlying_symbol: str = Field(..., example="MSFT", description="Symbol of the underlying stock")
    option_type: OptionType
    strike_price: Decimal = Field(..., max_digits=12, decimal_places=4)
    expiration_date: date
    name: Optional[str] = Field(None, example="MSFT $300 Call Exp 2025-12-19")


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    currency: Currency | None = None
    model_config = ConfigDict(extra='forbid')


class AssetRead(AssetBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # Include underlying asset info if it's an option
    underlying_asset: Optional[AssetReadBasic] = None # Loaded via relationship
    model_config = orm_config