import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Slot } from "@radix-ui/react-slot"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  [
    "inline-flex",
    "items-center",
    "justify-center",
    "gap-2",
    "whitespace-nowrap",
    "select-none",
    "rounded-control",
    "border",
    "text-ui",
    "font-semibold",
    "leading-ui",
    "cursor-pointer",
    "transition-[background-color,border-color,color,scale]",
    "duration-fast",
    "ease-standard",
    "active:scale-[0.96]",
    "disabled:pointer-events-none",
    "disabled:opacity-55"
  ],
  {
    variants: {
      variant: {
        primary: [
          "bg-accent-solid",
          "border-accent-solid",
          "text-accent-on-solid",
          "hover:bg-accent-solid-hover",
          "hover:border-accent-solid-hover",
          "active:bg-accent-solid-active",
          "active:border-accent-solid-active"
        ],
        secondary: [
          "bg-surface-raised",
          "border-edge-control",
          "text-content-primary",
          "hover:bg-surface-selected",
          "hover:border-accent-solid"
        ],
        ghost: [
          "bg-transparent",
          "border-transparent",
          "text-content-secondary",
          "hover:bg-surface-raised",
          "hover:text-content-primary"
        ],
        danger: [
          "bg-danger-solid",
          "border-danger-solid",
          "text-danger-on-solid",
          "hover:opacity-90"
        ]
      },
      size: {
        sm: ["min-h-[var(--control-height-sm)]", "px-2", "text-small", "gap-1.5"],
        md: ["min-h-[var(--control-height)]", "px-3"],
        lg: ["min-h-[var(--control-height-lg)]", "px-4", "text-body", "gap-2"]
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
