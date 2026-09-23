import * as React from "react"
import { ChevronDown } from "lucide-react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const selectVariants = cva(
  [
    "w-full",
    "min-w-0",
    "appearance-none",
    "rounded-control",
    "border",
    "bg-surface-input",
    "pl-2.5",
    "pr-8",
    "text-ui",
    "text-content-primary",
    "transition-[border-color]",
    "duration-fast",
    "ease-standard",
    "disabled:cursor-not-allowed",
    "disabled:opacity-55",
    "enabled:hover:border-accent-solid",
    "focus-visible:border-focus"
  ],
  {
    variants: {
      size: {
        sm: ["min-h-[var(--control-height-sm)]", "text-small"],
        md: ["min-h-[var(--control-height)]"],
        lg: ["min-h-[40px]", "text-body"]
      }
    },
    defaultVariants: {
      size: "md"
    }
  }
)

export interface SelectProps
  extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "size">,
    VariantProps<typeof selectVariants> {}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, size, children, ...props }, ref) => {
    return (
      <div className="relative">
        <select
          ref={ref}
          className={cn(selectVariants({ size, className }))}
          {...props}
        >
          {children}
        </select>
        <ChevronDown
          aria-hidden="true"
          className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-content-muted"
        />
      </div>
    )
  }
)
Select.displayName = "Select"

export { Select, selectVariants }
