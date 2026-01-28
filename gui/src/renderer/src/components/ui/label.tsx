import * as React from "react"
import * as LabelPrimitive from "@radix-ui/react-label"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const labelVariants = cva(
  // Base classes - consistent across all variants
  [
    "text-sm",
    "font-medium",
    "leading-none",
    "peer-disabled:cursor-not-allowed",
    "peer-disabled:opacity-70"
  ],
  {
    variants: {
      // Required field indicator
      required: {
        false: [],
        true: [
          "after:content-['*']",
          "after:ml-0.5",
          "after:text-error-500"
        ]
      }
    }
  }
)

export interface LabelProps
  extends React.ComponentPropsWithoutRef<typeof LabelPrimitive.Root>,
    VariantProps<typeof labelVariants> {}

const Label = React.forwardRef<
  React.ElementRef<typeof LabelPrimitive.Root>,
  LabelProps
>(({ className, required, ...props }, ref) => (
  <LabelPrimitive.Root
    ref={ref}
    className={cn(labelVariants({ required, className }))}
    {...props}
  />
))
Label.displayName = LabelPrimitive.Root.displayName

export { Label }
