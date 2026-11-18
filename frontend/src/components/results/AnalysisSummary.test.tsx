import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { VALID_EXPERIMENTAL_BATCH_SCORE } from "../../test/fixtures";
import { AnalysisSummary } from "./AnalysisSummary";

describe("analysis summary", () => {
  it("derives multi-wallet cards and chart values from the API response", () => {
    render(<AnalysisSummary result={VALID_EXPERIMENTAL_BATCH_SCORE} onDetails={() => undefined} onNewAnalysis={() => undefined} />);
    expect(screen.getByText("Wallets analyzed").parentElement).toHaveTextContent("3");
    expect(screen.getByText("Historical events").parentElement).toHaveTextContent("3");
    expect(screen.getByText("Selected for review").parentElement).toHaveTextContent("2");
    expect(screen.getByText("Highest score").parentElement).toHaveTextContent("0.630");
    expect(screen.getByRole("img", { name: "Anomaly score comparison for 3 wallets" })).toHaveTextContent("0.630");
    expect(screen.getByRole("img", { name: "Anomaly score comparison for 3 wallets" })).toHaveTextContent("0.510");
    expect(screen.getByRole("img", { name: "Anomaly score comparison for 3 wallets" })).toHaveTextContent("0.400");
  });

  it("adapts its language for one wallet and exposes both continuation actions", async () => {
    const user = userEvent.setup();
    const details = vi.fn();
    const clear = vi.fn();
    const wallet = VALID_EXPERIMENTAL_BATCH_SCORE.ranked_wallets[0];
    const single = {
      ...VALID_EXPERIMENTAL_BATCH_SCORE,
      wallets_submitted: 1,
      wallets_scored: 1,
      review_budget_requested: 1,
      review_budget: 1,
      review_candidates: [wallet.wallet],
      ranked_wallets: [wallet],
    };
    render(<AnalysisSummary result={single} onDetails={details} onNewAnalysis={clear} />);
    expect(screen.getByText("Wallet analyzed").parentElement).toHaveTextContent("1");
    expect(screen.getByText("Anomaly score").parentElement).toHaveTextContent("0.630");
    await user.click(screen.getByRole("button", { name: "View detailed analysis" }));
    await user.click(screen.getByRole("button", { name: "Start new analysis" }));
    expect(details).toHaveBeenCalledOnce();
    expect(clear).toHaveBeenCalledOnce();
  });
});
