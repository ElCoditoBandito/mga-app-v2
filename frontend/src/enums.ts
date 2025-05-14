/**
 * Centralized enum definitions for the frontend
 * These values are aligned with backend enum values in backend/models/enums.py
 */

/**
 * Types of cash transfers between accounts
 * Aligned with backend TransactionType enum
 */
export enum CashTransferType {
  BANK_TO_BROKERAGE = 'BankToBrokerage',         // Club Bank to Fund(s) Brokerage
  BROKERAGE_TO_BANK = 'BrokerageToBank',         // Fund Brokerage to Club Bank
  INTERFUND_CASH_TRANSFER = 'InterfundCashTransfer', // Between two Funds' brokerage cash
}

/**
 * Types of option transactions
 * Aligned with backend TransactionType enum
 */
export enum OptionTransactionType {
  BUY_TO_OPEN = 'BuyOption',       // Buy to Open
  SELL_TO_OPEN = 'SellOption',      // Sell to Open
  BUY_TO_CLOSE = 'CloseOptionBuy',  // Buy to Close
  SELL_TO_CLOSE = 'CloseOptionSell' // Sell to Close
}

/**
 * Types of options (calls or puts)
 * Aligned with backend OptionType enum
 */
export enum OptionType {
  CALL = 'Call',
  PUT = 'Put'
}

/**
 * Types of member transactions
 * Aligned with backend MemberTransactionType enum
 */
export enum MemberTransactionType {
  DEPOSIT = 'Deposit',
  WITHDRAWAL = 'Withdrawal',
}

/**
 * Types of transactions in the system
 * Aligned with backend TransactionType enum
 */
export enum TransactionType {
  BUY_STOCK = 'BuyStock',
  SELL_STOCK = 'SellStock',
  BUY_OPTION = 'BuyOption',
  SELL_OPTION = 'SellOption',
  DIVIDEND = 'Dividend',
  BROKERAGE_INTEREST = 'BrokerageInterest',
  CLUB_EXPENSE = 'ClubExpense',
  BANK_TO_BROKERAGE = 'BankToBrokerage',
  BROKERAGE_TO_BANK = 'BrokerageToBank',
  OPTION_EXPIRATION = 'OptionExpiration',
  OPTION_EXERCISE = 'OptionExercise',
  OPTION_ASSIGNMENT = 'OptionAssignment',
  BANK_INTEREST = 'BankInterest'
}

/**
 * Types of assets
 * Aligned with backend AssetType enum
 */
export enum AssetType {
  STOCK = 'Stock',
  OPTION = 'Option'
}

/**
 * Club member roles
 * Aligned with backend ClubRole enum
 */
export enum ClubRole {
  Admin = 'Admin',
  Member = 'Member',
  ReadOnly = 'ReadOnly'
}

/**
 * Currency codes
 * Aligned with backend Currency enum
 */
export enum Currency {
  USD = 'USD',
  EUR = 'EUR',
  GBP = 'GBP',
  JPY = 'JPY',
  CAD = 'CAD',
  AUD = 'AUD',
  CHF = 'CHF',
  NZD = 'NZD',
  HKD = 'HKD',
  SGD = 'SGD'
}