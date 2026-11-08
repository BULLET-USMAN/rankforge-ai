import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-rf-crimson disabled:pointer-events-none disabled:opacity-40 select-none",
  {
    variants: {
      variant: {
        default:
          "bg-rf-crimson text-rf-text shadow-sm hover:bg-rf-crimson-hover active:bg-rf-crimson-muted border border-transparent",
        secondary:
          "bg-rf-surface text-rf-text border border-rf-border hover:bg-rf-bg-secondary hover:text-white active:bg-rf-bg",
        outline:
          "border border-rf-border bg-transparent text-rf-text hover:bg-rf-surface hover:text-white",
        ghost:
          "text-rf-text-secondary hover:bg-rf-surface hover:text-rf-text",
        danger:
          "bg-rf-error text-white hover:bg-red-700 active:bg-red-800",
        link: "text-rf-text-secondary underline-offset-4 hover:underline hover:text-rf-text",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-5 text-base",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
