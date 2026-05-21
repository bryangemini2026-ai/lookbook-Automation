interface CircularProgressProps {
  value: number
  max?: number
  size?: number
  strokeWidth?: number
  label?: string
  showValue?: boolean
  color?: 'blue' | 'green' | 'yellow' | 'red'
}

const colorValues: Record<NonNullable<CircularProgressProps['color']>, string> = {
  blue: 'var(--color-accent-blue)',
  green: 'var(--color-accent-green)',
  yellow: 'var(--color-accent-yellow)',
  red: 'var(--color-accent-red)',
}

export default function CircularProgress({
  value,
  max = 100,
  size = 80,
  strokeWidth = 6,
  label,
  showValue = true,
  color = 'blue',
}: CircularProgressProps) {
  const percentage = max === 0 ? 0 : Math.max(0, Math.min(Math.round((value / max) * 100), 100))
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (percentage / 100) * circumference

  return (
    <div
      className="flex flex-col items-center gap-2"
      role="progressbar"
      aria-valuenow={percentage}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label || 'Progress'}
    >
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="transform -rotate-90"
          aria-hidden="true"
        >
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--color-surface-3)"
            strokeWidth={strokeWidth}
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={colorValues[color]}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-500 ease-out"
          />
        </svg>
        {showValue && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span
              className="font-mono font-semibold"
              style={{ fontSize: size * 0.2, color: 'var(--color-text-primary)' }}
            >
              {percentage}%
            </span>
          </div>
        )}
      </div>
      {label && (
        <span className="text-small" style={{ color: 'var(--color-text-secondary)' }}>
          {label}
        </span>
      )}
    </div>
  )
}
