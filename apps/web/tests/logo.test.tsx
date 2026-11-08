import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { Logo } from "@/components/brand/logo";

describe("Logo Component", () => {
  it("renders SVG geometry with aria-label", () => {
    render(<Logo size={32} />);
    const svg = screen.getByLabelText("RankForge Logo");
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveAttribute("width", "32");
  });

  it("renders brand text and AI badge by default", () => {
    render(<Logo />);
    expect(screen.getByText("RankForge")).toBeInTheDocument();
    expect(screen.getByText("AI")).toBeInTheDocument();
  });

  it("hides text when showText is false", () => {
    render(<Logo showText={false} />);
    expect(screen.queryByText("RankForge")).not.toBeInTheDocument();
  });
});
