import type { BatchWalletScore, FeatureReferenceStatistic, FeatureValue } from "../api/types";

export type WalletSort = "score" | "rank" | "events" | "history" | "wallet";

export interface WalletFilters {
  wallet: string;
  selectedOnly: boolean;
  warningsOnly: boolean;
  minEvents: number;
  minHistoryDays: number;
  minScore: number;
  maxScore: number;
}

export function filterAndSortWallets(
  wallets: BatchWalletScore[],
  filters: WalletFilters,
  sort: WalletSort,
): BatchWalletScore[] {
  const query = filters.wallet.trim().toLocaleLowerCase();
  const filtered = wallets.filter((wallet) =>
    (!query || wallet.wallet.toLocaleLowerCase().includes(query)) &&
    (!filters.selectedOnly || wallet.selected_for_review) &&
    (!filters.warningsOnly || wallet.warnings.length > 0) &&
    wallet.included_historical_event_count >= filters.minEvents &&
    wallet.observable_history_days >= filters.minHistoryDays &&
    wallet.anomaly_score >= filters.minScore &&
    wallet.anomaly_score <= filters.maxScore,
  );
  return filtered.sort((left, right) => {
    const order = sort === "score" ? right.anomaly_score - left.anomaly_score
      : sort === "rank" ? left.rank - right.rank
      : sort === "events" ? right.included_historical_event_count - left.included_historical_event_count
      : sort === "history" ? right.observable_history_days - left.observable_history_days
      : left.wallet.localeCompare(right.wallet);
    return order || left.rank - right.rank || left.wallet.localeCompare(right.wallet);
  });
}

export interface ScoreBin { minimum: number; maximum: number; count: number }

export function scoreDistribution(wallets: BatchWalletScore[]): { kind: "dots" | "histogram"; bins: ScoreBin[] } {
  if (wallets.length < 5) {
    return { kind: "dots", bins: wallets.map((wallet) => ({ minimum: wallet.anomaly_score, maximum: wallet.anomaly_score, count: 1 })) };
  }
  const values = wallets.map((wallet) => wallet.anomaly_score);
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const binCount = Math.min(8, Math.max(4, Math.ceil(Math.sqrt(values.length))));
  if (minimum === maximum) return { kind: "histogram", bins: [{ minimum, maximum, count: values.length }] };
  const width = (maximum - minimum) / binCount;
  const bins = Array.from({ length: binCount }, (_, index) => ({
    minimum: minimum + index * width,
    maximum: index === binCount - 1 ? maximum : minimum + (index + 1) * width,
    count: 0,
  }));
  values.forEach((value) => {
    const index = Math.min(binCount - 1, Math.floor((value - minimum) / width));
    bins[index].count += 1;
  });
  return { kind: "histogram", bins };
}

export function robustComparison(value: FeatureValue, reference: FeatureReferenceStatistic): string {
  if (value === null) return "Unavailable: wallet value is missing";
  if (reference.is_binary) return `Training true share ${(reference.mean * 100).toFixed(1)}%`;
  if (reference.is_constant || reference.quartile_3 === reference.quartile_1) return "Unavailable: training IQR is zero";
  if (typeof value !== "number") return "Unavailable for non-numeric value";
  const distance = (value - reference.median) / (reference.quartile_3 - reference.quartile_1);
  return `${distance >= 0 ? "+" : ""}${distance.toFixed(2)} training IQR from median`;
}

export function shortWallet(wallet: string): string {
  return wallet.length <= 18 ? wallet : `${wallet.slice(0, 8)}…${wallet.slice(-6)}`;
}
