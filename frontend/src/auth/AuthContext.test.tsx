import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { useAuth } from "./AuthContext";
import { authGateway, renderWithAuth } from "../test/auth";

function AuthenticationProbe() {
  const { user, loading, error, signIn, signOut } = useAuth();
  return (
    <div>
      <span>{loading ? "loading" : user?.email ?? "signed-out"}</span>
      <button onClick={() => void signIn()}>sign in</button>
      <button onClick={() => void signOut()}>sign out</button>
      {error && <p role="alert">{error}</p>}
    </div>
  );
}

describe("authentication context", () => {
  it("observes sign-in and sign-out state changes", async () => {
    const user = userEvent.setup();
    renderWithAuth(<AuthenticationProbe />, authGateway(null));
    expect(await screen.findByText("signed-out")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "sign in" }));
    expect(await screen.findByText("approved@example.test")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "sign out" }));
    expect(await screen.findByText("signed-out")).toBeInTheDocument();
  });

  it("renders a safe accessible error when popup sign-in fails", async () => {
    const user = userEvent.setup();
    const gateway = authGateway(null);
    gateway.signIn = vi.fn().mockRejectedValue(new Error("sensitive provider detail"));
    renderWithAuth(<AuthenticationProbe />, gateway);
    await screen.findByText("signed-out");
    await user.click(screen.getByRole("button", { name: "sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Unable to sign in");
    expect(screen.getByRole("alert")).not.toHaveTextContent("sensitive provider detail");
  });
});
