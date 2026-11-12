import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FEATURE_NAMES } from "../api/types";
import { VALID_PREVIEW } from "../test/fixtures";
import { FeatureCharts } from "./FeatureCharts";
import { FeatureResults } from "./FeatureResults";

describe("feature presentation", () => {
  it("renders every registered feature and distinguishes unavailable values from zero", () => {
    render(<FeatureResults preview={VALID_PREVIEW} />);
    for (const name of FEATURE_NAMES) expect(screen.getByText(name)).toBeInTheDocument();
    expect(screen.getAllByText("Unavailable")).toHaveLength(3);
    expect(screen.getByText("Missing fee proportion").closest("article")).toHaveTextContent("0.0%");
  });

  it("gives each chart an accessible text alternative based on returned values", () => {
    render(<FeatureCharts preview={VALID_PREVIEW} />);
    expect(screen.getByRole("img", { name: /Observed activity: Events 1/ })).toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: "30-day history coverage" })).toHaveAttribute("aria-valuenow", "80");
    expect(screen.getByText(/not thresholds or risk indicators/)).toBeInTheDocument();
  });
});
