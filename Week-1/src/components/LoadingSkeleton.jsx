export default function LoadingSkeleton({ className = '', lines = 3 }) {
  return (
    <div className={`animate-pulse space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          style={{
            backgroundColor: 'var(--bg-input)',
            height: '0.75rem',
            width: i === lines - 1 ? '60%' : '100%',
            borderRadius: 'var(--radius)',
          }}
        />
      ))}
    </div>
  )
}

export function CardSkeleton() {
  return (
    <div
      className="data-panel animate-pulse"
    >
      <div className="flex gap-4">
        <div
          className="w-36 h-36 flex-shrink-0"
          style={{ backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius)' }}
        />
        <div className="flex-1 space-y-2">
          <div
            className="h-4 w-24"
            style={{ backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius)' }}
          />
          <div
            className="h-3 w-16"
            style={{ backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius)' }}
          />
          <div className="flex gap-1.5">
            <div
              className="h-5 w-12"
              style={{ backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius)' }}
            />
          </div>
          <div className="space-y-1.5 mt-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="flex items-center gap-2">
                <div
                  className="w-7 h-2"
                  style={{ backgroundColor: 'var(--bg-input)' }}
                />
                <div
                  className="flex-1 h-2"
                  style={{ backgroundColor: 'var(--bg-input)' }}
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
