import React, { useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle2, X, XCircle } from 'lucide-react'

export type ToastType = 'success' | 'error' | 'warning'

export interface ToastProps {
  id: string
  type: ToastType
  message: string
  onClose: (id: string) => void
}

const TOAST_ICONS: Record<ToastType, JSX.Element> = {
  success: <CheckCircle2 size={18} aria-hidden="true" />,
  error: <XCircle size={18} aria-hidden="true" />,
  warning: <AlertTriangle size={18} aria-hidden="true" />,
}

const Toast: React.FC<ToastProps> = ({ id, type, message, onClose }) => {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    // Trigger animation frame to ensure transition happens
    requestAnimationFrame(() => {
      setIsVisible(true)
    })
  }, [])

  const handleClose = () => {
    setIsVisible(false)
    // Wait for animation to finish before removing
    setTimeout(() => {
      onClose(id)
    }, 300)
  }

  return (
    <div className="toast" data-tone={type} data-visible={isVisible} role="alert">
      <span className="toast-icon">{TOAST_ICONS[type]}</span>
      <div className="toast-message">{message}</div>
      <button
        type="button"
        className="icon-button ml-auto"
        onClick={handleClose}
        aria-label="Close"
      >
        <X size={15} aria-hidden="true" />
      </button>
    </div>
  )
}

export default Toast
