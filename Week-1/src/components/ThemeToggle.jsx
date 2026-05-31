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
    <button
      onClick={() => setIsWireframe((v) => !v)}
      className="px-3 py-1 cursor-pointer uppercase tracking-wider transition-colors"
      style={{
        backgroundColor: 'var(--bg-input)',
        color: 'var(--text-secondary)',
        border: '1px var(--border-style) var(--border-color)',
        borderRadius: 'var(--radius)',
        fontFamily: 'var(--font-pixel)',
        fontSize: '0.4rem',
      }}
      aria-label="Toggle theme"
    >
      {isWireframe ? 'VIBRANT' : 'BLUEPRINT'}
    </button>
  )
}
