import { forwardRef, ReactNode } from 'react'
import { cn } from '../../lib/utils'

interface OverlayContainerProps {
  children: ReactNode
  className?: string
}

export const OverlayContainer = forwardRef<HTMLDivElement, OverlayContainerProps>(
  function OverlayContainer({ children, className }, ref) {
    const handleMouseEnter = (): void => {
      // When mouse enters the interactive zone, stop ignoring mouse events
      // so the user can click buttons
      window.api?.setIgnoreMouseEvents(false)
    }

    const handleMouseLeave = (): void => {
      // When mouse leaves the interactive zone, ignore mouse events again
      // forwarding them to the underlying window
      window.api?.setIgnoreMouseEvents(true, { forward: true })
    }

    return (
      <div
        ref={ref}
        className={cn('p-2 transition-all duration-200', className)}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {children}
      </div>
    )
  }
)
