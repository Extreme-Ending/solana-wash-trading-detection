import { describe, expect, it } from "vitest";
import type { BatchWalletScore, FeatureReferenceStatistic } from "../api/types";
import { VALID_EXPERIMENTAL_BATCH_SCORE } from "../test/fixtures";
import { filterAndSortWallets, robustComparison, scoreDistribution } from "./anomalyDashboard";

const wallets = VALID_EXPERIMENTAL_BATCH_SCORE.ranked_wallets;
const filters = { wallet: "", selectedOnly: false, warningsOnly: false, minEvents: 0, minHistoryDays: 0, minScore: 0, maxScore: 1 };

describe("anomaly dashboard transformations", () => {
  it("filters without mutating original rank or score and combines criteria", () => {
    const visible = filterAndSortWallets(wallets, { ...filters, selectedOnly: true, minHistoryDays: 6 }, "wallet");
    expect(visible.map((wallet) => wallet.wallet)).toEqual(["wallet-a"]);
    expect(visible[0]).toMatchObject({ rank: 1, anomaly_score: 0.63 });
    expect(wallets.map((wallet) => wallet.rank)).toEqual([1, 2, 3]);
  });

  it("sorts deterministically by event count, history, wallet, score, and rank", () => {
    for (const sort of ["events", "history", "wallet", "score", "rank"] as const) {
      const result = filterAndSortWallets(wallets, filters, sort);
      expect(result).toHaveLength(3);
      expect(new Set(result.map((wallet) => wallet.wallet)).size).toBe(3);
    }
  });

  it("uses dots for small batches and exact-count histogram bins for larger batches", () => {
    expect(scoreDistribution(wallets).kind).toBe("dots");
    const larger: BatchWalletScore[] = Array.from({ length: 9 }, (_, index) => ({
      ...wallets[0], wallet: `wallet-${index}`, rank: index + 1, anomaly_score: index / 10,
    }));
    const distribution = scoreDistribution(larger);
    expect(distribution.kind).toBe("histogram");
    expect(distribution.bins.reduce((sum, bin) => sum + bin.count, 0)).toBe(9);
  });

  it("handles missing, binary, zero-IQR, and ordinary feature comparisons", () => {
    const reference: FeatureReferenceStatistic = { observed_count: 40, missing_count: 0, minimum: 0, quartile_1: 1, median: 2, mean: 2, quartile_3: 3, maximum: 4, is_binary: false, is_constant: false };
    expect(robustComparison(4, reference)).toContain("+1.00");
    expect(robustComparison(null, reference)).toContain("missing");
    expect(robustComparison(true, { ...reference, mean: 0.25, is_binary: true })).toContain("25.0%");
    expect(robustComparison(2, { ...reference, quartile_1: 2, quartile_3: 2, is_constant: true })).toContain("IQR is zero");
  });
});
