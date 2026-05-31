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
      className="px-3 py-1.5 cursor-pointer uppercase tracking-wider transition-all"
      style={{
        background: 'linear-gradient(180deg, var(--shell-dark) 0%, var(--shell-bevel-dark) 100%)',
        color: '#ccc',
        border: '2px solid var(--shell-dark)',
        borderRadius: '4px',
        fontFamily: 'var(--font-pixel)',
        fontSize: '0.38rem',
        boxShadow: '0 2px 0 var(--shell-bevel-dark), inset 0 1px 0 rgba(255,255,255,0.08)',
      }}
      aria-label="Toggle theme"
    >
      {isWireframe ? 'VIBRANT' : 'BLUEPRINT'}
    </button>
  )
}
