import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse, MODEL_NOT_APPROVED, VALID_EXPERIMENTAL_SCORE, VALID_REQUEST } from "../test/fixtures";
import { ModelStatus } from "./ModelStatus";
import { renderWithAuth } from "../test/auth";

describe("model gate", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("keeps the scoring check disabled until a validated request exists", () => {
    renderWithAuth(<ModelStatus request={null} />);
    expect(screen.getByRole("button", { name: "Request experimental score" })).toBeDisabled();
    expect(screen.queryByText(/anomaly_score/i)).not.toBeInTheDocument();
  });

  it("treats the structured scoring 503 as expected unavailability", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(MODEL_NOT_APPROVED, 503)));
    renderWithAuth(<ModelStatus request={VALID_REQUEST} />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Request experimental score" })).toBeEnabled());
    await user.click(screen.getByRole("button", { name: "Request experimental score" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Prediction capability is unavailable");
  });

  it("renders a real experimental score without probability formatting", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(VALID_EXPERIMENTAL_SCORE)));
    renderWithAuth(<ModelStatus request={VALID_REQUEST} />);
    const button = await screen.findByRole("button", { name: "Request experimental score" });
    await waitFor(() => expect(button).toBeEnabled());
    await user.click(button);
    const result = await screen.findByRole("status", { name: "Experimental anomaly score" });
    expect(result).toHaveTextContent("0.413245");
    expect(result).toHaveTextContent("model-specific, unitless");
    expect(result).toHaveTextContent("not a probability or fraud determination");
    expect(result).not.toHaveTextContent("%");
  });

  it("shows protected-endpoint authorization errors", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({
      error: { code: "USER_NOT_ALLOWED", message: "Not permitted", details: null },
    }, 403)));
    renderWithAuth(<ModelStatus request={VALID_REQUEST} />);
    const button = await screen.findByRole("button", { name: "Request experimental score" });
    await waitFor(() => expect(button).toBeEnabled());
    await user.click(button);
    expect(await screen.findByRole("status")).toHaveTextContent("not approved for this API");
  });
});
