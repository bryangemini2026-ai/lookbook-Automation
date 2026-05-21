interface ProgressBarProps {
  value: number
  max?: number
  label?: string
  showPercentage?: boolean
  size?: 'sm' | 'md' | 'lg'
  color?: 'blue' | 'green' | 'yellow' | 'red'
}

const colorClasses: Record<'blue' | 'green' | 'yellow' | 'red', string> = {
  blue: 'bg-[var(--color-accent-blue)]',
  green: 'bg-[var(--color-accent-green)]',
  yellow: 'bg-[var(--color-accent-yellow)]',
  red: 'bg-[var(--color-accent-red)]',
}

const sizeClasses: Record<'sm' | 'md' | 'lg', string> = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-3',
}

export default function ProgressBar({
  value,
  max = 100,
  label,
  showPercentage = true,
  size = 'md',
  color = 'blue',
}: ProgressBarProps) {
  const percentage = max === 0 ? 0 : Math.max(0, Math.min(Math.round((value / max) * 100), 100))

  return (
    <div className="w-full">
      {(label || showPercentage) && (
        <div className="flex justify-between items-center mb-2">
          {label && (
            <span className="text-small" style={{ color: 'var(--color-text-secondary)' }}>
              {label}
            </span>
          )}
          {showPercentage && (
            <span className="text-small font-mono" style={{ color: 'var(--color-text-muted)' }}>
              {percentage}%
            </span>
          )}
        </div>
      )}
      <div
        className={`w-full rounded-full overflow-hidden ${sizeClasses[size]}`}
        style={{ background: 'var(--color-surface-3)' }}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={label || 'Progress'}
      >
        <div
          className={`${colorClasses[color]} rounded-full transition-all duration-500 ease-out ${sizeClasses[size]}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
