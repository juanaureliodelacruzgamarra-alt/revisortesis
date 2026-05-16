import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/cn";

const buttonVariants = cva(
  // `whitespace-nowrap` keeps labels on a single line so two-word CTAs like
  // "Reporte ejecutivo (PDF)" don't wrap inside a fixed-height button.
  // `shrink-0` prevents flex parents from squashing the button when the sibling
  // text takes most of the row width.
  "inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium leading-none transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-950 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 dark:focus-visible:ring-violet-400 dark:focus-visible:ring-offset-[#0b0e2a]",
  {
    variants: {
      variant: {
        default: cn(
          "bg-zinc-900 text-zinc-50 hover:bg-zinc-900/90",
          // Aurora: violet gradient with subtle glow
          "dark:bg-gradient-to-br dark:from-violet-600 dark:to-violet-400 dark:text-white dark:shadow-[0_8px_24px_-10px_rgba(124,58,237,0.6)] dark:hover:from-violet-500 dark:hover:to-violet-300",
        ),
        outline: cn(
          "border border-zinc-200 bg-white hover:bg-zinc-100 hover:text-zinc-900",
          "dark:border-[color:rgba(196,181,253,0.3)] dark:bg-transparent dark:text-[color:var(--aurora-cream)] dark:hover:border-[color:rgba(196,181,253,0.55)] dark:hover:bg-[rgba(124,58,237,0.12)]",
        ),
        ghost: cn(
          "hover:bg-zinc-100 hover:text-zinc-900",
          "dark:text-[color:var(--aurora-cream)] dark:hover:bg-[rgba(124,58,237,0.12)]",
        ),
        destructive: cn(
          "bg-rose-600 text-white hover:bg-rose-700",
          "dark:bg-rose-500/90 dark:hover:bg-rose-500",
        ),
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 px-3",
        lg: "h-11 px-6",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
