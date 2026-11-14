import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ErrorPage from "../app/error";
import { StatePanel } from "../app/state-panel";

describe("workspace states", () => {
  it("announces loading", () => {
    render(
      <StatePanel state="loading" title="Loading workspace">
        <p>Please wait.</p>
      </StatePanel>,
    );
    expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
  });
  it("provides a working retry without displaying error internals", () => {
    const retry = vi.fn();
    render(<ErrorPage reset={retry} />);
    expect(screen.getByRole("alert")).toHaveTextContent("could not be loaded");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(retry).toHaveBeenCalledOnce();
  });
  it("explains unavailable access", () => {
    render(
      <StatePanel state="forbidden" title="Access unavailable">
        <p>This view cannot be opened.</p>
      </StatePanel>,
    );
    expect(screen.getByRole("heading")).toHaveTextContent("Access unavailable");
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
