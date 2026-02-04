import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const inputVariants = cva(
  // Base classes - consistent across all variants
  [
    "flex",
    "h-10",
    "w-full",
    "rounded-token-md",
    "border",
    "border-border-default",
    "bg-bg-secondary",
    "px-3",
    "py-2",
    "text-sm",
    "text-text-primary",
    "placeholder:text-text-tertiary",
    "transition-colors-spring",
    "focus-visible:outline-none",
    "focus-visible:shadow-focus",
    "focus-visible:border-transparent",
    "disabled:cursor-not-allowed",
    "disabled:opacity-50"
  ],
  {
    variants: {
      // Validation state
      state: {
        default: [
          "border-border-default"
        ],
        error: [
          "border-error-500",
          "text-error-500",
          "placeholder:text-error-500/70",
          "focus-visible:shadow-[0_0_0_2px_rgba(239,68,68,0.5)]"
        ]
      },
      // Size variants
      size: {
        sm: ["h-9", "px-2", "text-xs"],
        md: ["h-10", "px-3"],
        lg: ["h-11", "px-4", "text-base"]
      }
    },
    defaultVariants: {
      state: "default",
      size: "md"
    }
  }
)

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement>,
    VariantProps<typeof inputVariants> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, state, size, type = "text", ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(inputVariants({ state, size, className }))}
        ref={ref}
        aria-invalid={state === "error"}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
