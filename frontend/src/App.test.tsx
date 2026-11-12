import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { FEATURE_NAMES } from "./api/types";
import { App } from "./App";
import { jsonResponse, MODEL_NOT_APPROVED, VALID_PREVIEW } from "./test/fixtures";

function installApiMock() {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith("/healthz")) {
      return Promise.resolve(jsonResponse({ status: "ok", service: "Solana Wallet Feature Service", version: "0.1.0" }));
    }
    if (url.endsWith("/readyz") || url.endsWith("/v1/score")) {
      return Promise.resolve(jsonResponse(MODEL_NOT_APPROVED, 503));
    }
    if (url.endsWith("/v1/features/preview")) return Promise.resolve(jsonResponse(VALID_PREVIEW));
    return Promise.resolve(jsonResponse({ error: { code: "NOT_FOUND", message: "Not found", details: null } }, 404));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("application", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("renders the research boundary, navigation, and independent service states", async () => {
    installApiMock();
    render(<App />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Inspect wallet behaviour");
    expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeInTheDocument();
    expect(screen.getByText("No verified wash-trading labels")).toBeInTheDocument();
    expect(screen.getByText("Experimental and not served")).toBeInTheDocument();
    expect(await screen.findByText("Solana Wallet Feature Service v0.1.0")).toBeInTheDocument();
    expect(await screen.findByText("Unavailable by design")).toBeInTheDocument();
  });

  it("completes the synthetic preview flow and displays the exact feature registry", async () => {
    const user = userEvent.setup();
    installApiMock();
    render(<App />);
    await user.click(screen.getByRole("button", { name: "Load synthetic example" }));
    await user.click(screen.getByRole("button", { name: "Generate feature preview" }));
    expect(await screen.findByRole("heading", { name: "All 29 descriptive wallet features" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getAllByText(/^[a-z0-9_]+$/).length).toBeGreaterThanOrEqual(FEATURE_NAMES.length));
    expect(screen.getByText("These descriptive features do not establish wash trading or fraud.")).toBeInTheDocument();
    expect(screen.queryByText(/fraud probability/i)).not.toBeInTheDocument();
  });
});
