import * as React from "react"
import { Label } from "./label"
import { cn } from "@/lib/utils"

export interface FieldProps extends React.HTMLAttributes<HTMLDivElement> {
  label?: React.ReactNode
  htmlFor?: string
  hint?: React.ReactNode
  error?: React.ReactNode
  required?: boolean
}

function Field({
  label,
  htmlFor,
  hint,
  error,
  required,
  className,
  children,
  ...props
}: FieldProps): JSX.Element {
  const generatedId = React.useId()
  const control = React.isValidElement(children)
    ? (children as React.ReactElement<React.HTMLAttributes<HTMLElement>>)
    : null
  const controlId = htmlFor ?? (control?.props.id || generatedId)
  const hintId = hint ? `${controlId}-hint` : undefined
  const errorId = error ? `${controlId}-error` : undefined
  const describedBy =
    [control?.props["aria-describedby"], errorId ?? hintId].filter(Boolean).join(" ") || undefined

  const wired = control
    ? React.cloneElement(control, {
        id: controlId,
        "aria-describedby": describedBy,
        ...(error ? { "aria-invalid": true } : {})
      })
    : children

  return (
    <div className={cn("flex flex-col gap-1", className)} {...props}>
      {label !== undefined && (
        <Label htmlFor={controlId} required={required}>
          {label}
        </Label>
      )}
      {wired}
      {error ? (
        <p id={errorId} className="text-caption text-danger-text">
          {error}
        </p>
      ) : hint ? (
        <p id={hintId} className="text-caption text-content-muted">
          {hint}
        </p>
      ) : null}
    </div>
  )
}

export { Field }
