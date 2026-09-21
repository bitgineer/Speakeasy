import * as React from "react"
import { type LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

export interface IconProps {
  icon: LucideIcon
  className?: string
  size?: number
  color?: string
  strokeWidth?: number
}

export function Icon({ icon: IconComponent, className, size = 24, color, strokeWidth, ...props }: IconProps) {
  return (
    <IconComponent
      size={size}
      color={color}
      strokeWidth={strokeWidth}
      className={cn("inline-block", className)}
      {...props}
    />
  )
}
