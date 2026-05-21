type StatusType = 'active' | 'processing' | 'pending' | 'error' | 'idle' | 'completed'

interface StatusIndicatorProps {
  status: StatusType
  label?: string
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

const statusConfig: Record<StatusType, { class: string; label: string }> = {
  active: { class: 'status-dot-active', label: 'Active' },
  processing: { class: 'status-dot-processing', label: 'Processing' },
  pending: { class: 'status-dot-pending', label: 'Pending' },
  error: { class: 'status-dot-error', label: 'Error' },
  idle: { class: 'status-dot-idle', label: 'Idle' },
  completed: { class: 'status-dot-active', label: 'Completed' },
}

const sizeClasses: Record<'sm' | 'md' | 'lg', string> = {
  sm: 'w-2 h-2',
  md: 'w-2.5 h-2.5',
  lg: 'w-3 h-3',
}

export default function StatusIndicator({
  status,
  label,
  size = 'md',
  showLabel = true,
}: StatusIndicatorProps) {
  const config = statusConfig[status]

  return (
    <div className="flex items-center gap-2">
      <span
        className={`status-dot ${config.class} ${sizeClasses[size]}`}
        role="img"
        aria-label={label || config.label}
      />
      {showLabel && (
        <span className="text-small" style={{ color: 'var(--color-text-secondary)' }}>
          {label || config.label}
        </span>
      )}
    </div>
  )
}
