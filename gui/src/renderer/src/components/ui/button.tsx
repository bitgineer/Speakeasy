import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Slot } from "@radix-ui/react-slot"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  // Base classes - consistent across all variants
  [
    "inline-flex",
    "items-center",
    "justify-center",
    "whitespace-nowrap",
    "rounded-lg",
    "text-sm",
    "font-medium",
    "transition-all",
    "duration-200",
    "ease-out",
    "focus-visible:outline-none",
    "focus-visible:shadow-focus",
    "disabled:pointer-events-none",
    "disabled:opacity-50",
    "cursor-pointer",
    "select-none"
  ],
  {
    variants: {
      // Intent variants
      variant: {
        primary: [
          "bg-[var(--color-accent)]",
          "text-[var(--color-text-on-accent)]",
          "hover:bg-[var(--color-accent-hover)]",
          "hover:shadow-lg",
          "hover:scale-[1.02]",
          "active:scale-[0.98]",
          "shadow-md"
        ],
        secondary: [
          "bg-[var(--color-bg-tertiary)]",
          "text-[var(--color-text-primary)]",
          "border",
          "border-[var(--color-border)]",
          "hover:bg-[var(--color-bg-elevated)]",
          "hover:border-[var(--color-border-strong)]",
          "hover:shadow-md",
          "hover:scale-[1.01]",
          "active:scale-[0.99]"
        ],
        ghost: [
          "bg-transparent",
          "text-[var(--color-text-secondary)]",
          "hover:bg-[var(--color-bg-tertiary)]",
          "hover:text-[var(--color-text-primary)]",
          "hover:scale-[1.01]",
          "active:scale-[0.99]"
        ],
        danger: [
          "bg-[var(--color-error)]",
          "text-white",
          "hover:bg-[var(--color-error-hover)]",
          "hover:shadow-lg",
          "hover:scale-[1.02]",
          "active:scale-[0.98]"
        ]
      },
      // Size variants
      size: {
        sm: ["h-8", "px-3", "text-xs", "gap-1.5"],
        md: ["h-10", "px-4", "gap-2"],
        lg: ["h-12", "px-6", "text-base", "gap-2"]
      }
    },
    defaultVariants: {
      variant: "primary",
      size: "md"
    }
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
