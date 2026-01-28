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
    "rounded-token-md",
    "text-sm",
    "font-medium",
    "transition-all-spring",
    "focus-visible:outline-none",
    "focus-visible:shadow-focus",
    "disabled:pointer-events-none",
    "disabled:opacity-50"
  ],
  {
    variants: {
      // Intent variants
      variant: {
        primary: [
          "bg-primary-500",
          "text-[var(--color-text-on-primary)]",
          "hover:bg-primary-600",
          "active:bg-primary-700",
          "hover-lift"
        ],
        secondary: [
          "bg-bg-tertiary",
          "text-[var(--color-text-primary)]",
          "border",
          "border-border-default",
          "hover:bg-bg-elevated",
          "hover-elevated"
        ],
        ghost: [
          "hover:bg-bg-tertiary",
          "hover:text-[var(--color-text-primary)]",
          "hover-lift"
        ],
        danger: [
          "bg-error-500",
          "text-white",
          "hover:bg-error-600",
          "active:bg-error-700",
          "hover-lift"
        ]
      },
      // Size variants
      size: {
        sm: ["h-9", "px-3", "text-xs"],
        md: ["h-10", "px-4"],
        lg: ["h-11", "px-8", "text-base"]
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
