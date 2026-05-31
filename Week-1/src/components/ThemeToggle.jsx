import { useState, useEffect } from 'react'

export default function ThemeToggle() {
  const [isWireframe, setIsWireframe] = useState(() => {
    return localStorage.getItem('pokearena-theme') === 'wireframe'
  })

  useEffect(() => {
    const root = document.documentElement
    if (isWireframe) {
      root.classList.add('wireframe')
      localStorage.setItem('pokearena-theme', 'wireframe')
    } else {
      root.classList.remove('wireframe')
      localStorage.setItem('pokearena-theme', 'vibrant')
    }
  }, [isWireframe])

  return (
    <div className="flex items-center gap-2 text-xs">
      <span style={{ color: isWireframe ? 'var(--text-primary)' : 'var(--text-muted)' }}>
        Blueprint
      </span>
      <button
        onClick={() => setIsWireframe((v) => !v)}
        className="relative w-10 h-5 rounded-full transition-colors cursor-pointer"
        style={{
          backgroundColor: isWireframe ? 'var(--text-muted)' : 'var(--accent)',
        }}
        aria-label="Toggle theme"
      >
        <span
          className="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform"
          style={{
            left: '2px',
            transform: isWireframe ? 'translateX(0)' : 'translateX(20px)',
          }}
        />
      </button>
      <span style={{ color: isWireframe ? 'var(--text-muted)' : 'var(--text-primary)' }}>
        Vibrant
      </span>
    </div>
  )
}
