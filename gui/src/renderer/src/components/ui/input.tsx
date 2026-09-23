import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const inputVariants = cva(
  [
    "flex",
    "w-full",
    "min-w-0",
    "rounded-control",
    "border",
    "bg-surface-input",
    "px-2.5",
    "text-ui",
    "text-content-primary",
    "placeholder:text-content-muted",
    "transition-[border-color]",
    "duration-fast",
    "ease-standard",
    "disabled:cursor-not-allowed",
    "disabled:opacity-55"
  ],
  {
    variants: {
      state: {
        default: ["border-edge-control", "enabled:hover:border-accent-solid", "focus-visible:border-focus"],
        error: ["border-danger-solid", "focus-visible:border-danger-solid"]
      },
      size: {
        sm: ["min-h-[var(--control-height-sm)]", "text-small"],
        md: ["min-h-[var(--control-height)]"],
        lg: ["min-h-[40px]", "text-body"]
      }
    },
    defaultVariants: {
      state: "default",
      size: "md"
    }
  }
)

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'>,
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
