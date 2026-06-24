import {
  getTrainerAnalyticsOverview,
  getTrainerContentAnalytics,
  getTrainerSalesAnalytics,
  type TrainerAnalyticsOverview,
  type TrainerContentAnalyticsResponse,
  type TrainerSalesAnalyticsResponse,
} from '@/modules/trainer-analytics/api';
import {
  getTrainerRevenueSummary,
  getTrainerRevenueTransactions,
  type TrainerRevenueListResponse,
  type TrainerRevenueSummary,
  type TrainerRevenueTransaction,
} from '@/modules/trainer-revenue/api';

export type TrainerSalesDashboardSnapshot = {
  overview: TrainerAnalyticsOverview;
  content: TrainerContentAnalyticsResponse;
  sales: TrainerSalesAnalyticsResponse;
  revenue: TrainerRevenueSummary;
  transactions: TrainerRevenueListResponse<TrainerRevenueTransaction>;
};

export const trainerSalesApi = {
  async getSnapshot(days = 30, limit = 50): Promise<TrainerSalesDashboardSnapshot> {
    const [overview, content, sales, revenue, transactions] = await Promise.all([
      getTrainerAnalyticsOverview(days),
      getTrainerContentAnalytics('all', days, limit),
      getTrainerSalesAnalytics(days, limit),
      getTrainerRevenueSummary(days),
      getTrainerRevenueTransactions(limit),
    ]);

    return {
      overview,
      content,
      sales,
      revenue,
      transactions,
    };
  },
};
