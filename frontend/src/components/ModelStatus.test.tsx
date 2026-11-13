import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse, MODEL_NOT_APPROVED, VALID_REQUEST } from "../test/fixtures";
import { ModelStatus } from "./ModelStatus";
import { renderWithAuth } from "../test/auth";

describe("model gate", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("keeps the scoring check disabled until a validated request exists", () => {
    renderWithAuth(<ModelStatus request={null} />);
    expect(screen.getByRole("button", { name: "Check scoring gate with last request" })).toBeDisabled();
    expect(screen.queryByText(/anomaly_score/i)).not.toBeInTheDocument();
  });

  it("treats the structured scoring 503 as expected unavailability", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(MODEL_NOT_APPROVED, 503)));
    renderWithAuth(<ModelStatus request={VALID_REQUEST} />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Check scoring gate with last request" })).toBeEnabled());
    await user.click(screen.getByRole("button", { name: "Check scoring gate with last request" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Prediction capability is unavailable");
  });
});
