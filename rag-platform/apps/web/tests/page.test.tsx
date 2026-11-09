import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Home from "../app/page";

describe("foundation overview", () => {
  it("explains the actual availability instead of offering fake connections", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Your company’s knowledge",
    );
    expect(screen.getByLabelText("Implementation status")).toHaveTextContent(
      "question answering are not available yet",
    );
    expect(
      screen.queryByRole("button", { name: /connect|ask/i }),
    ).not.toBeInTheDocument();
    expect(screen.getAllByText("Planned")).toHaveLength(3);
    expect(
      screen.getByRole("link", { name: /explore the roadmap/i }),
    ).toHaveAttribute("href", "#getting-started");
  });
});
