# enums.py
import enum

class ClubRole(str, enum.Enum):
    ADMIN = "Admin"
    MEMBER = "Member"
    READ_ONLY = "ReadOnly"

class AssetType(str, enum.Enum):
    STOCK = "Stock" # Includes ETFs for DB purposes
    OPTION = "Option"
    # CASH is not an asset type here, it's tracked separately

class OptionType(str, enum.Enum):
    CALL = "Call"
    PUT = "Put"

class TransactionType(str, enum.Enum):

    # Club Actions
    CLUB_EXPENSE = "ClubExpense"                     # Club pays expense from Club Bank Account
    BANK_TO_BROKERAGE = "BankToBrokerage"   # Transfer cash Club Bank -> Fund(s) Brokerage
    BROKERAGE_TO_BANK = "BrokerageToBank"   # Transfer cash Fund(s) Brokerage -> Club Bank

    # Investment Actions - Stocks/ETFs
    BUY_STOCK = "BuyStock"
    SELL_STOCK = "SellStock"
    DIVIDEND = "Dividend"                   # Cash dividend received
    BANK_INTEREST = "BankInterest"
    BROKERAGE_INTEREST = "BrokerageInterest"
    
    # Maybe add STOCK_DIVIDEND, SPLIT later if needed

    # Investment Actions - Options
    BUY_OPTION = "BuyOption"                # BuyToOpen Call or Put
    SELL_OPTION = "SellOption"              # SellToOpen Call or Put
    CLOSE_OPTION_BUY = "CloseOptionBuy"     # BuyToClose Short Option
    CLOSE_OPTION_SELL = "CloseOptionSell"   # SellToClose Long Option
    OPTION_EXPIRATION = "OptionExpiration"  # Option expired worthless
    OPTION_EXERCISE = "OptionExercise"      # Long option exercised
    OPTION_ASSIGNMENT = "OptionAssignment"  # Short option assigned

    # Internal Transfers & Adjustments
    INTERFUND_CASH_TRANSFER = "InterfundCashTransfer" # Move cash between funds
    INTERFUND_POSITION_TRANSFER = "InterfundPositionTransfer" # Move stock/option between funds (will likely generate linked Buy/Sell)
    ADJUSTMENT = "Adjustment"               # Generic adjustment or correction start
    REVERSAL = "Reversal"                   # Reversing a previous transaction during correction

class MemberTransactionType(str, enum.Enum):
    DEPOSIT = "Deposit"                     # Member adds cash to Club Bank Account
    WITHDRAWAL = "Withdrawal"               # Member removes cash from Club Bank Account (via Units)

class Currency(str, enum.Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    CHF = "CHF"
    NZD = "NZD"
    HKD = "HKD"
    SGD = "SGD"