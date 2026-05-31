export default function LoadingSkeleton({ className = '', lines = 3 }) {
  return (
    <div className={`animate-pulse space-y-3 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="rounded"
          style={{
            backgroundColor: 'var(--bg-input)',
            height: '1rem',
            width: i === lines - 1 ? '60%' : '100%',
          }}
        />
      ))}
    </div>
  )
}

export function CardSkeleton() {
  return (
    <div
      className="rounded-xl p-5 animate-pulse"
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px var(--border-style) var(--border-color)',
      }}
    >
      <div
        className="w-48 h-48 mx-auto mb-4 rounded-lg"
        style={{ backgroundColor: 'var(--bg-input)' }}
      />
      <div
        className="h-5 w-32 mx-auto mb-2 rounded"
        style={{ backgroundColor: 'var(--bg-input)' }}
      />
      <div className="flex justify-center gap-2 mb-4">
        <div
          className="h-6 w-16 rounded-full"
          style={{ backgroundColor: 'var(--bg-input)' }}
        />
      </div>
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <div
              className="w-8 h-3 rounded"
              style={{ backgroundColor: 'var(--bg-input)' }}
            />
            <div
              className="flex-1 h-3 rounded-full"
              style={{ backgroundColor: 'var(--bg-input)' }}
            />
          </div>
        ))}
      </div>
    </div>
  )
}
