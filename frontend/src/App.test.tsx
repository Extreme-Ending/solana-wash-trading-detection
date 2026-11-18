import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { authGateway, renderWithAuth } from "./test/auth";
import { jsonResponse, VALID_EXPERIMENTAL_BATCH_SCORE } from "./test/fixtures";

describe("redesigned application", () => {
  afterEach(() => {
    window.location.hash = "";
    vi.unstubAllGlobals();
  });

  it("presents Google sign-in without exposing an email/password form", async () => {
    const user = userEvent.setup();
    renderWithAuth(<App />, authGateway(null));

    expect(await screen.findByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Sign in to Wallet Insights" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continue with Google" })).toBeInTheDocument();
    expect(screen.queryByLabelText(/password/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Continue with Google" }));
    expect(await screen.findByRole("heading", { name: "Check a wallet" })).toBeInTheDocument();
  });

  it("renders one protected workflow and a truthful pre-analysis state", async () => {
    renderWithAuth(<App />);

    expect(await screen.findByRole("heading", { name: "Check a wallet" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Analyze wallets" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Historical events are required" })).toBeInTheDocument();
    expect(screen.getByText(/does not look up live wallet activity/i)).toBeInTheDocument();
    expect(screen.queryByText(/wallet balance/i)).not.toBeInTheDocument();
  });

  it("loads labelled demonstration data, submits an authenticated batch, and opens analytics", async () => {
    const user = userEvent.setup();
    const revisedBudget = {
      ...VALID_EXPERIMENTAL_BATCH_SCORE,
      review_budget_requested: 1,
      review_budget: 1,
      review_candidates: ["wallet-a"],
      ranked_wallets: VALID_EXPERIMENTAL_BATCH_SCORE.ranked_wallets.map((wallet) => ({
        ...wallet,
        selected_for_review: wallet.rank === 1,
      })),
    };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse(VALID_EXPERIMENTAL_BATCH_SCORE))
      .mockResolvedValueOnce(jsonResponse(revisedBudget));
    vi.stubGlobal("fetch", fetchMock);
    renderWithAuth(<App />);

    await user.click(await screen.findByRole("button", { name: "Use demonstration data" }));
    expect(screen.getByRole("status")).toHaveTextContent(/synthetic histories/i);
    await user.click(screen.getByRole("button", { name: "Analyze wallets" }));

    expect(await screen.findByRole("heading", { name: "Analysis summary" })).toBeInTheDocument();
    expect(screen.getByText(/do not confirm fraud or wash trading/i)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const request = fetchMock.mock.calls[0][1] as RequestInit;
    expect(request.headers).toMatchObject({ Authorization: "Bearer valid-test-firebase-token" });

    await user.click(screen.getByRole("button", { name: "View detailed analysis" }));
    expect(await screen.findByRole("heading", { name: "Analytics" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Wallet ranking" })).toBeInTheDocument();
    await waitFor(() => expect(window.location.hash).toBe("#analytics"));

    await user.clear(screen.getByLabelText("Wallets to select"));
    await user.type(screen.getByLabelText("Wallets to select"), "1");
    await user.click(screen.getByRole("button", { name: "Update capacity" }));
    expect(await screen.findByText(/updated from a new authenticated API response/i)).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const revisedRequest = JSON.parse(String((fetchMock.mock.calls[1][1] as RequestInit).body));
    expect(revisedRequest.review_budget).toBe(1);
  });
});
