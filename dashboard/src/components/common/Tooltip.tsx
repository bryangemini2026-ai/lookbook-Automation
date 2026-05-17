import { useState, useRef, type ReactNode } from 'react'

interface TooltipProps {
  text: string
  children: ReactNode
  position?: 'top' | 'bottom' | 'left' | 'right'
}

export default function Tooltip({ text, children, position = 'top' }: TooltipProps) {
  const [show, setShow] = useState(false)
  const timeoutRef = useRef<number>()

  const handleEnter = () => {
    timeoutRef.current = window.setTimeout(() => setShow(true), 400)
  }

  const handleLeave = () => {
    clearTimeout(timeoutRef.current)
    setShow(false)
  }

  const posClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  }

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
    >
      {children}
      {show && (
        <span
          className={`absolute ${posClasses[position]} z-50 px-3 py-2 text-xs text-gray-200 bg-gray-800 border border-gray-700 rounded-lg shadow-lg whitespace-nowrap pointer-events-none animate-in fade-in duration-200`}
        >
          {text}
        </span>
      )}
    </span>
  )
}
