import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded px-2 py-0.5 text-xs font-medium transition-colors select-none",
  {
    variants: {
      variant: {
        default:
          "border border-rf-border bg-rf-surface text-rf-text",
        secondary:
          "border border-rf-border/40 bg-rf-bg text-rf-text-secondary",
        crimson:
          "border border-rf-crimson/30 bg-rf-crimson/15 text-red-200",
        success:
          "border border-green-800/40 bg-green-950/40 text-green-300",
        warning:
          "border border-amber-800/40 bg-amber-950/40 text-amber-300",
        error:
          "border border-red-800/40 bg-red-950/40 text-red-300",
        outline:
          "border border-rf-border text-rf-text-secondary bg-transparent",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
