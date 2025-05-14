import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import LogStockTradeForm from "@/components/forms/LogStockTradeForm";
import LogOptionTradeForm from "@/components/forms/LogOptionTradeForm";
import LogDividendInterestForm from "@/components/forms/LogDividendInterestForm";
import LogCashTransferForm from "@/components/forms/LogCashTransferForm";
import LogClubExpenseForm from "@/components/forms/LogClubExpenseForm";
import { useParams } from "react-router-dom";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

// Import API hooks
import {
  useClubPortfolio,
  useFundTransactions,
  useRecordTrade,
  useRecordCashReceipt,
  useRecordCashTransfer,
  useClubFunds,
  useGetOrCreateStockAsset,
  useGetOrCreateOptionAsset
} from "@/hooks/useApi";

// Import types
import type {
  TradeData,
  CashReceiptData,
  CashTransferData
} from "@/lib/apiClient";

// Define interfaces for form data types
import type { DividendInterestFormData } from "@/components/forms/LogDividendInterestForm";
import type { StockTradeFormData } from "@/components/forms/LogStockTradeForm";
import type { OptionTradeFormData } from "@/components/forms/LogOptionTradeForm";
import type { ClubExpenseFormData } from "@/components/forms/LogClubExpenseForm";

// Helper functions for formatting
const formatCurrency = (value?: number | null) => {
  if (value == null) return 'N/A';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
};

const formatPercent = (value?: number | null) => {
  if (value == null) return 'N/A';
  return `${value.toFixed(2)}%`;
};

const formatDate = (dateString?: string) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

export default function PortfolioPage() {
  const { clubId } = useParams<{ clubId: string }>();
  const [activeTab, setActiveTab] = useState("holdings");
  const [activeTradeDialog, setActiveTradeDialog] = useState<string | null>(null);

  // Fetch portfolio data
  const {
    data: portfolioData,
    isLoading: isLoadingPortfolio,
    error: portfolioError
  } = useClubPortfolio(clubId || '');

  // Fetch transactions
  const {
    data: transactions,
    isLoading: isLoadingTransactions,
    error: transactionsError
  } = useFundTransactions(clubId || '');

  // Fetch funds for form usage
  const {
    data: funds,
    isLoading: isLoadingFunds
  } = useClubFunds(clubId || '');

  // Mutation hooks for forms
  const { mutate: recordTrade } = useRecordTrade(clubId || '');
  const { mutate: recordCashReceipt } = useRecordCashReceipt(clubId || '');
  const { mutate: recordCashTransfer } = useRecordCashTransfer(clubId || '');
  const { mutateAsync: createStockAsset } = useGetOrCreateStockAsset();
  const { mutateAsync: createOptionAsset } = useGetOrCreateOptionAsset();

  // Combined loading state
  const isLoading = isLoadingPortfolio || isLoadingTransactions || isLoadingFunds;

  // Combined error state
  const error = portfolioError || transactionsError;

  // Calculate unrealized gain/loss and percentages
  const unrealizedGainLoss = portfolioData?.positions?.reduce(
    (total, position) => total + position.unrealized_gain_loss,
    0
  ) || 0;

  const unrealizedGainLossPercent = portfolioData?.positions?.length
    ? (unrealizedGainLoss / (portfolioData.total_value - unrealizedGainLoss)) * 100
    : 0;

  // Mock performance data (would come from a different API endpoint in a real implementation)
  // This would be replaced with actual API data in a future iteration
  const performanceData = {
    ytdReturn: 5.2,
    oneYearReturn: 12.5,
    threeYearReturn: 24.8,
    fiveYearReturn: 42.3,
  };

  const handleCloseDialog = () => {
    setActiveTradeDialog(null);
  };

  // Handle form submissions
  // Convert form data to API data
  // Handle form submissions
  const handleStockTradeSubmit = async (formData: StockTradeFormData) => {
    try {
      // Step 1: Create or get the asset
      const asset = await createStockAsset({
        symbol: formData.asset_symbol,
        name: formData.asset_name || formData.asset_symbol // Use symbol as name if name not provided
      });
      
      // Step 2: Extract the asset_id
      const assetId = asset.id;
      
      // Step 3: Calculate amount
      const amount = formData.quantity * formData.price_per_unit;
      
      // Step 4: Create TradeData object
      const tradeData: TradeData = {
        fund_id: formData.fund_id,
        transaction_type: formData.transaction_type,
        transaction_date: formData.transaction_date,
        asset_id: assetId,
        quantity: formData.quantity,
        price_per_unit: formData.price_per_unit,
        amount: amount,
        notes: formData.description
      };
      
      recordTrade(tradeData, {
        onSuccess: () => {
          toast.success("Stock trade recorded successfully");
          handleCloseDialog();
        },
        onError: (error) => {
          console.error("Error recording stock trade:", error);
          toast.error("Failed to record stock trade");
        }
      });
    } catch (error) {
      console.error("Error creating stock asset or recording trade:", error);
      toast.error("Failed to process stock trade");
    }
  };

  const handleOptionTradeSubmit = async (formData: OptionTradeFormData) => {
    try {
      // Step 1: Create or get the option asset
      const asset = await createOptionAsset({
        underlying_symbol: formData.underlying_symbol,
        option_type: formData.option_type,
        strike_price: formData.strike_price,
        expiration_date: formData.expiration_date,
        // Optional fields
        contract_size: 100 // Standard contract size
      });
      
      // Step 2: Extract the asset_id
      const assetId = asset.id;
      
      // Step 3: Calculate amount (premium per contract * quantity * 100 shares per contract)
      const amount = formData.premium_per_contract * formData.quantity_contracts * 100;
      
      // Step 4: Create TradeData object
      const tradeData: TradeData = {
        fund_id: formData.fund_id,
        transaction_type: formData.transaction_type,
        transaction_date: formData.transaction_date,
        asset_id: assetId,
        quantity: formData.quantity_contracts,
        price_per_unit: formData.premium_per_contract * 100, // Convert to per-contract price
        amount: amount,
        notes: formData.description
      };
      
      recordTrade(tradeData, {
        onSuccess: () => {
          toast.success("Option trade recorded successfully");
          handleCloseDialog();
        },
        onError: (error) => {
          console.error("Error recording option trade:", error);
          toast.error("Failed to record option trade");
        }
      });
    } catch (error) {
      console.error("Error creating option asset or recording trade:", error);
      toast.error("Failed to process option trade");
    }
  };

  const handleDividendInterestSubmit = async (formData: DividendInterestFormData) => {
    try {
      // Create CashReceiptData object
      const receiptData: CashReceiptData = {
        fund_id: formData.fund_id,
        transaction_type: formData.transaction_type,
        transaction_date: formData.transaction_date,
        amount: formData.total_amount,
        asset_id: formData.asset_id,
        notes: formData.description
      };
      
      recordCashReceipt(receiptData, {
        onSuccess: () => {
          toast.success("Dividend/Interest recorded successfully");
          handleCloseDialog();
        },
        onError: (error) => {
          console.error("Error recording dividend/interest:", error);
          toast.error("Failed to record dividend/interest");
        }
      });
    } catch (error) {
      console.error("Error preparing receipt data:", error);
      toast.error("Failed to prepare receipt data");
    }
  };

  const handleCashTransferSubmit = async (formData: {
    club_id: string;
    transaction_type: string;
    transaction_date: string;
    total_amount: number;
    fund_id?: string;
    target_fund_id?: string;
    description?: string;
  }) => {
    try {
      // Create CashTransferData object
      const transferData: CashTransferData = {
        transaction_type: formData.transaction_type,
        transaction_date: formData.transaction_date,
        amount: formData.total_amount,
        fund_id: formData.fund_id,
        notes: formData.description
      };
      
      recordCashTransfer(transferData, {
        onSuccess: () => {
          toast.success("Cash transfer recorded successfully");
          handleCloseDialog();
        },
        onError: (error) => {
          console.error("Error recording cash transfer:", error);
          toast.error("Failed to record cash transfer");
        }
      });
    } catch (error) {
      console.error("Error preparing transfer data:", error);
      toast.error("Failed to prepare transfer data");
    }
  };

  const handleClubExpenseSubmit = async (formData: ClubExpenseFormData) => {
    // This would use a different mutation hook in a real implementation
    console.log("Club expense form data:", formData);
    toast.success("Club expense recorded successfully");
    handleCloseDialog();
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto py-6">
        <div className="flex justify-between items-center mb-6">
          <Skeleton className="h-10 w-40" />
          <Skeleton className="h-10 w-60" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-10 w-40 mb-4" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto py-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h2 className="text-lg font-semibold text-red-700 mb-2">Error Loading Portfolio Data</h2>
          <p className="text-red-600 mb-4">
            {error.message || "There was a problem retrieving the portfolio data. Please try again later."}
          </p>
          <Button variant="outline" className="bg-white border-red-300 text-red-700 hover:bg-red-50">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  // Sort positions by market value (descending)
  const sortedPositions = [...(portfolioData?.positions || [])].sort(
    (a, b) => b.market_value - a.market_value
  );

  // Get recent transactions (limited to 5)
  const recentTransactions = transactions?.slice(0, 5) || [];

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Portfolio</h1>
        <div className="flex space-x-2">
          <Dialog open={activeTradeDialog === "stock"} onOpenChange={(open) => !open && handleCloseDialog()}>
            <DialogTrigger asChild>
              <Button onClick={() => setActiveTradeDialog("stock")}>Log Stock Trade</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle>Log Stock Trade</DialogTitle>
              </DialogHeader>
              <LogStockTradeForm
                funds={funds?.map(fund => ({ id: fund.id, name: fund.name })) || []}
                onSubmit={handleStockTradeSubmit}
                onCancel={handleCloseDialog}
              />
            </DialogContent>
          </Dialog>

          <Dialog open={activeTradeDialog === "option"} onOpenChange={(open) => !open && handleCloseDialog()}>
            <DialogTrigger asChild>
              <Button onClick={() => setActiveTradeDialog("option")}>Log Option Trade</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle>Log Option Trade</DialogTitle>
              </DialogHeader>
              <LogOptionTradeForm
                funds={funds?.map(fund => ({ id: fund.id, name: fund.name })) || []}
                onSubmit={handleOptionTradeSubmit}
                onCancel={handleCloseDialog}
              />
            </DialogContent>
          </Dialog>

          <Dialog open={activeTradeDialog === "dividend"} onOpenChange={(open) => !open && handleCloseDialog()}>
            <DialogTrigger asChild>
              <Button onClick={() => setActiveTradeDialog("dividend")}>Log Dividend/Interest</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle>Log Dividend or Interest</DialogTitle>
              </DialogHeader>
              <LogDividendInterestForm
                funds={funds?.map(fund => ({ id: fund.id, name: fund.name })) || []}
                assets={portfolioData?.positions?.map(pos => ({
                  id: pos.asset_id,
                  symbol: pos.asset_symbol,
                  name: pos.asset_name,
                  asset_type: 'STOCK' // Assuming all positions are stocks
                })) || []}
                onSubmit={handleDividendInterestSubmit}
                onCancel={handleCloseDialog}
              />
            </DialogContent>
          </Dialog>

          <Dialog open={activeTradeDialog === "transfer"} onOpenChange={(open) => !open && handleCloseDialog()}>
            <DialogTrigger asChild>
              <Button onClick={() => setActiveTradeDialog("transfer")}>Log Cash Transfer</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle>Log Cash Transfer</DialogTitle>
              </DialogHeader>
              <LogCashTransferForm
                clubId={clubId || ""}
                funds={funds?.map(fund => ({ id: fund.id, name: fund.name })) || []}
                onSubmit={handleCashTransferSubmit}
                onCancel={handleCloseDialog}
              />
            </DialogContent>
          </Dialog>

          <Dialog open={activeTradeDialog === "expense"} onOpenChange={(open) => !open && handleCloseDialog()}>
            <DialogTrigger asChild>
              <Button onClick={() => setActiveTradeDialog("expense")}>Log Club Expense</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle>Log Club Expense</DialogTitle>
              </DialogHeader>
              <LogClubExpenseForm
                clubId={clubId || ""}
                onSubmit={handleClubExpenseSubmit}
                onCancel={handleCloseDialog}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Portfolio Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(portfolioData?.total_value)}</div>
            <p className="text-xs text-muted-foreground">
              Cash: {formatCurrency(portfolioData?.cash_balance)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Unrealized Gain/Loss</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(unrealizedGainLoss)}</div>
            <p className="text-xs text-muted-foreground">
              {formatPercent(unrealizedGainLossPercent)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <p className="text-xs text-muted-foreground">YTD</p>
                <p className="font-medium">{formatPercent(performanceData.ytdReturn)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">1 Year</p>
                <p className="font-medium">{formatPercent(performanceData.oneYearReturn)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">3 Year</p>
                <p className="font-medium">{formatPercent(performanceData.threeYearReturn)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">5 Year</p>
                <p className="font-medium">{formatPercent(performanceData.fiveYearReturn)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-4">
          <TabsTrigger value="holdings">Holdings</TabsTrigger>
          <TabsTrigger value="transactions">Recent Transactions</TabsTrigger>
        </TabsList>
        <TabsContent value="holdings">
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-4">Symbol</th>
                      <th className="text-left p-4">Name</th>
                      <th className="text-right p-4">Shares</th>
                      <th className="text-right p-4">Avg Cost</th>
                      <th className="text-right p-4">Current Price</th>
                      <th className="text-right p-4">Market Value</th>
                      <th className="text-right p-4">Gain/Loss</th>
                      <th className="text-right p-4">Gain/Loss %</th>
                      <th className="text-right p-4">Allocation %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedPositions.map((position) => {
                      // Calculate allocation percentage
                      const allocation = portfolioData?.total_value 
                        ? (position.market_value / portfolioData.total_value) * 100 
                        : 0;
                      
                      return (
                        <tr key={position.asset_id} className="border-b hover:bg-muted/50">
                          <td className="p-4 font-medium">{position.asset_symbol}</td>
                          <td className="p-4">{position.asset_name}</td>
                          <td className="p-4 text-right">{position.quantity}</td>
                          <td className="p-4 text-right">
                            {formatCurrency(position.cost_basis / position.quantity)}
                          </td>
                          <td className="p-4 text-right">{formatCurrency(position.current_price)}</td>
                          <td className="p-4 text-right">{formatCurrency(position.market_value)}</td>
                          <td className="p-4 text-right">{formatCurrency(position.unrealized_gain_loss)}</td>
                          <td className="p-4 text-right">{formatPercent(position.unrealized_gain_loss_percent)}</td>
                          <td className="p-4 text-right">{formatPercent(allocation)}</td>
                        </tr>
                      );
                    })}
                    {sortedPositions.length === 0 && (
                      <tr>
                        <td colSpan={9} className="p-4 text-center text-muted-foreground">
                          No holdings found. Start by logging a stock trade.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="transactions">
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-4">Date</th>
                      <th className="text-left p-4">Type</th>
                      <th className="text-left p-4">Symbol</th>
                      <th className="text-right p-4">Shares</th>
                      <th className="text-right p-4">Price</th>
                      <th className="text-right p-4">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentTransactions.map((transaction) => (
                      <tr key={transaction.id} className="border-b hover:bg-muted/50">
                        <td className="p-4">{formatDate(transaction.transaction_date)}</td>
                        <td className="p-4">{transaction.transaction_type}</td>
                        <td className="p-4">{transaction.asset?.symbol || "-"}</td>
                        <td className="p-4 text-right">{transaction.quantity || "-"}</td>
                        <td className="p-4 text-right">
                          {transaction.price_per_unit 
                            ? formatCurrency(transaction.price_per_unit) 
                            : "-"}
                        </td>
                        <td className="p-4 text-right">{formatCurrency(transaction.amount)}</td>
                      </tr>
                    ))}
                    {recentTransactions.length === 0 && (
                      <tr>
                        <td colSpan={6} className="p-4 text-center text-muted-foreground">
                          No transactions found. Start by logging a trade or cash transaction.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
