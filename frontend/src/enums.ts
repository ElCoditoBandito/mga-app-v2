/**
 * Centralized enum definitions for the frontend
 * These values are aligned with backend enum values in backend/models/enums.py
 */

/**
 * Types of cash transfers between accounts
 * Aligned with backend TransactionType enum
 */
export enum CashTransferType {
  BANK_TO_BROKERAGE = 'BANK_TO_BROKERAGE',         // Club Bank to Fund(s) Brokerage
  BROKERAGE_TO_BANK = 'BROKERAGE_TO_BANK',         // Fund Brokerage to Club Bank
  INTERFUND_CASH_TRANSFER = 'INTERFUND_CASH_TRANSFER', // Between two Funds' brokerage cash
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
  DEPOSIT = 'DEPOSIT',
  WITHDRAWAL = 'WITHDRAWAL',
}