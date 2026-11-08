import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { Button } from "@/components/ui/button";

describe("Button Component", () => {
  it("renders with default crimson styling", () => {
    render(<Button>Click Action</Button>);
    const btn = screen.getByRole("button", { name: "Click Action" });
    expect(btn).toBeInTheDocument();
    expect(btn.className).toContain("bg-rf-crimson");
  });

  it("renders secondary variant", () => {
    render(<Button variant="secondary">Secondary Action</Button>);
    const btn = screen.getByRole("button", { name: "Secondary Action" });
    expect(btn.className).toContain("bg-rf-surface");
  });

  it("respects disabled attribute", () => {
    render(<Button disabled>Disabled Action</Button>);
    const btn = screen.getByRole("button", { name: "Disabled Action" });
    expect(btn).toBeDisabled();
    expect(btn.className).toContain("disabled:opacity-40");
  });
});
