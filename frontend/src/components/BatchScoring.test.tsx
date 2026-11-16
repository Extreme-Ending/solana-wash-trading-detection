import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { authGateway, renderWithAuth } from "../test/auth";
import {
  jsonResponse,
  MODEL_NOT_APPROVED,
  VALID_EXPERIMENTAL_BATCH_SCORE,
} from "../test/fixtures";
import { BatchScoring } from "./BatchScoring";

describe("batch scoring", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("requires authentication while allowing local synthetic input", async () => {
    const user = userEvent.setup();
    renderWithAuth(<BatchScoring />, authGateway(null));
    await screen.findByText(/sign in with an approved Google account/i);
    expect(screen.getByRole("button", { name: "Request batch ranking" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Load synthetic batch" }));
    expect(
      (screen.getByLabelText("Wallet histories (JSON array)") as HTMLTextAreaElement).value,
    ).toContain("synthetic-wallet-bursty");
  });

  it("renders ranked scores, the review budget, and the interpretation boundary", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(VALID_EXPERIMENTAL_BATCH_SCORE)));
    renderWithAuth(<BatchScoring />);
    await user.click(screen.getByRole("button", { name: "Load synthetic batch" }));
    const submit = screen.getByRole("button", { name: "Request batch ranking" });
    await waitFor(() => expect(submit).toBeEnabled());
    await user.click(submit);
    expect(await screen.findByText("wallet-a")).toBeInTheDocument();
    expect(screen.getByText("0.630000")).toBeInTheDocument();
    expect(screen.getAllByText("Review candidate")).toHaveLength(2);
    expect(screen.getByText(/less than seven days of observable history/i)).toBeInTheDocument();
    expect(screen.getByText(/not confirmed wash trading or fraud/i)).toBeInTheDocument();
    expect(screen.getByText(/not probabilities/i)).toBeInTheDocument();
  });

  it("exposes an accessible loading state while the protected request is pending", async () => {
    const user = userEvent.setup();
    let resolveResponse: (response: Response) => void = () => undefined;
    vi.stubGlobal("fetch", vi.fn().mockImplementation(() => new Promise<Response>((resolve) => {
      resolveResponse = resolve;
    })));
    renderWithAuth(<BatchScoring />);
    await user.click(screen.getByRole("button", { name: "Load synthetic batch" }));
    const submit = screen.getByRole("button", { name: "Request batch ranking" });
    await waitFor(() => expect(submit).toBeEnabled());
    await user.click(submit);
    expect(screen.getByRole("button", { name: "Ranking wallets…" })).toBeDisabled();
    resolveResponse(jsonResponse(VALID_EXPERIMENTAL_BATCH_SCORE));
    expect(await screen.findByText("wallet-a")).toBeInTheDocument();
  });

  it("renders explicit wallet-local rejections without hiding ranked results", async () => {
    const user = userEvent.setup();
    const partial = {
      ...VALID_EXPERIMENTAL_BATCH_SCORE,
      wallets_submitted: 4,
      wallets_rejected: 1,
      rejected_wallets: [{
        wallet: "wallet-empty",
        code: "EMPTY_WALLET_HISTORY",
        message: "No events were supplied for this wallet.",
        supplied_event_count: 0,
      }],
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(partial)));
    renderWithAuth(<BatchScoring />);
    await user.click(screen.getByRole("button", { name: "Load synthetic batch" }));
    const submit = screen.getByRole("button", { name: "Request batch ranking" });
    await waitFor(() => expect(submit).toBeEnabled());
    await user.click(submit);
    expect(await screen.findByRole("heading", { name: "Rejected wallet histories" })).toBeInTheDocument();
    expect(screen.getByText("wallet-empty")).toBeInTheDocument();
    expect(screen.getByText("EMPTY_WALLET_HISTORY")).toBeInTheDocument();
    expect(screen.getByText("wallet-a")).toBeInTheDocument();
  });

  it("shows disabled model availability without inventing results", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(MODEL_NOT_APPROVED, 503)));
    renderWithAuth(<BatchScoring />);
    await user.click(screen.getByRole("button", { name: "Load synthetic batch" }));
    const submit = screen.getByRole("button", { name: "Request batch ranking" });
    await waitFor(() => expect(submit).toBeEnabled());
    await user.click(submit);
    expect(await screen.findByRole("status")).toHaveTextContent("Prediction capability is unavailable");
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it.each([
    [401, "INVALID_TOKEN", "sign-in session is missing or expired"],
    [403, "USER_NOT_ALLOWED", "not approved for this API"],
    [503, "AUTH_VERIFICATION_UNAVAILABLE", "verification is temporarily unavailable"],
  ])("renders safe authentication handling for HTTP %i", async (status, code, expected) => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({
      error: { code, message: "Sensitive provider detail", details: null },
    }, status)));
    renderWithAuth(<BatchScoring />);
    await user.click(screen.getByRole("button", { name: "Load synthetic batch" }));
    const submit = screen.getByRole("button", { name: "Request batch ranking" });
    await waitFor(() => expect(submit).toBeEnabled());
    await user.click(submit);
    expect(await screen.findByRole("status")).toHaveTextContent(expected);
    expect(screen.queryByText("Sensitive provider detail")).not.toBeInTheDocument();
  });
});
