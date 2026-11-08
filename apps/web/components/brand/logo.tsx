import React from "react";
import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  size?: number;
  showText?: boolean;
  compactText?: boolean;
}

export function Logo({ className, size = 24, showText = true, compactText = false }: LogoProps) {
  return (
    <div className={cn("inline-flex items-center gap-2.5 select-none", className)}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="flex-shrink-0"
        aria-label="RankForge Logo"
      >
        {/* Diamond foundation grid */}
        <rect
          x="3"
          y="3"
          width="26"
          height="26"
          rx="5"
          fill="#191A1E"
          stroke="#34353A"
          strokeWidth="1.5"
        />
        {/* Geometric RF upward search / forge mark */}
        {/* Vertical stem */}
        <path
          d="M10 9V23"
          stroke="#E9E9EC"
          strokeWidth="2.2"
          strokeLinecap="round"
        />
        {/* R upper loop / Forge anvil facet */}
        <path
          d="M10 9H17.5C19.433 9 21 10.567 21 12.5C21 14.433 19.433 16 17.5 16H10"
          stroke="#9F1733"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Upward diagonal growth beam */}
        <path
          d="M15 16L21.5 23"
          stroke="#9F1733"
          strokeWidth="2.2"
          strokeLinecap="round"
        />
        {/* Precision focal crossbar indicator */}
        <path
          d="M10 16H15"
          stroke="#E9E9EC"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
      {showText && (
        <span className="font-semibold tracking-tight text-rf-text text-[15px] flex items-center gap-1.5">
          <span>{compactText ? "RankForge" : "RankForge"}</span>
          {!compactText && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rf-surface border border-rf-border text-rf-text-secondary tracking-wider uppercase">
              AI
            </span>
          )}
        </span>
      )}
    </div>
  );
}
