import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  [
    "inline-flex",
    "items-center",
    "gap-1",
    "rounded-pill",
    "border",
    "px-2",
    "py-0.5",
    "text-label",
    "font-semibold",
    "uppercase",
    "tracking-[var(--tracking-label)]",
    "whitespace-nowrap"
  ],
  {
    variants: {
      variant: {
        default: [
          "border-edge-subtle",
          "bg-surface-sunken",
          "text-content-secondary"
        ],
        primary: [
          "border-accent-border",
          "bg-accent-muted",
          "text-accent-text"
        ],
        success: [
          "border-success-border",
          "bg-success-muted",
          "text-success-text"
        ],
        warning: [
          "border-warning-border",
          "bg-warning-muted",
          "text-warning-text"
        ],
        error: [
          "border-danger-border",
          "bg-danger-muted",
          "text-danger-text"
        ],
        info: [
          "border-accent-border",
          "bg-accent-muted",
          "text-accent-text"
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
