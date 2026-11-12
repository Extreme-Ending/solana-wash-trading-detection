import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { EventWorkbench } from "./EventWorkbench";
import { jsonResponse, VALID_PREVIEW } from "../test/fixtures";

describe("event workbench", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("loads clearly synthetic input and submits the exact one-wallet request", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(VALID_PREVIEW));
    vi.stubGlobal("fetch", fetchMock);
    const onPreview = vi.fn();
    render(<EventWorkbench onPreview={onPreview} onClear={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Load synthetic example" }));
    expect(screen.getByLabelText("Wallet identifier")).toHaveValue("synthetic-wallet-demo-001");
    expect(screen.getByLabelText("Scoring timestamp (UTC)")).toHaveValue("2025-02-01T00:00:00Z");

    await user.click(screen.getByRole("button", { name: "Generate feature preview" }));
    await waitFor(() => expect(onPreview).toHaveBeenCalledOnce());
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(String(init.body)) as { events: Array<{ wallet: string }> };
    expect(body.events).toHaveLength(3);
    expect(body.events.every((event) => event.wallet === "synthetic-wallet-demo-001")).toBe(true);
    expect(screen.getByRole("status")).toHaveTextContent("Preview generated");
  });

  it("reports client-side errors without contacting the API", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    render(<EventWorkbench onPreview={vi.fn()} onClear={vi.fn()} />);

    await user.type(screen.getByLabelText("Wallet identifier"), "wallet-one");
    await user.type(screen.getByLabelText("Scoring timestamp (UTC)"), "2025-02-01T03:00:00+03:00");
    await user.click(screen.getByRole("button", { name: "Generate feature preview" }));
    expect(screen.getByRole("status")).toHaveTextContent("must be a valid ISO-8601 UTC value");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("surfaces backend failures without inventing an output", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    const onPreview = vi.fn();
    render(<EventWorkbench onPreview={onPreview} onClear={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: "Load synthetic example" }));
    await user.click(screen.getByRole("button", { name: "Generate feature preview" }));
    expect(await screen.findByRole("status")).toHaveTextContent("backend could not be reached");
    expect(onPreview).not.toHaveBeenCalled();
  });
});
