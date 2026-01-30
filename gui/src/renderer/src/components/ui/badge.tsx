import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  // Base classes - consistent across all variants
  [
    "inline-flex",
    "items-center",
    "rounded-full",
    "border",
    "px-2.5",
    "py-0.5",
    "text-xs",
    "font-medium",
    "transition-colors-spring",
    "focus:outline-none",
    "focus:ring-2",
    "focus:ring-offset-2",
    "focus:ring-offset-bg-primary"
  ],
  {
    variants: {
      // Semantic color variants
      variant: {
        default: [
          "border-border-default",
          "bg-bg-tertiary",
          "text-text-primary",
          "hover:bg-bg-elevated"
        ],
        primary: [
          "border-transparent",
          "bg-primary-500",
          "text-text-on-primary",
          "hover:bg-primary-600"
        ],
        success: [
          "border-transparent",
          "bg-success-500",
          "text-text-on-primary",
          "hover:bg-success-600"
        ],
        warning: [
          "border-transparent",
          "bg-warning-500",
          "text-text-on-dark",
          "hover:bg-warning-600"
        ],
        error: [
          "border-transparent",
          "bg-error-500",
          "text-text-on-primary",
          "hover:bg-error-600"
        ],
        info: [
          "border-transparent",
          "bg-info-500",
          "text-text-on-primary",
          "hover:bg-info-600"
        ]
      }
    },
    defaultVariants: {
      variant: "default"
    }
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
