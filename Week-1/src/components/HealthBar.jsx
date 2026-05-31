import { motion } from 'framer-motion'

export default function HealthBar({ name, current, max }) {
  const pct = Math.max(0, (current / max) * 100)
  const color = pct > 50 ? 'var(--success)' : pct > 20 ? 'var(--warning)' : 'var(--danger)'

  return (
    <div
      className="rounded-lg p-3 flex-1"
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px var(--border-style) var(--border-color)',
      }}
    >
      <div className="flex justify-between mb-1">
        <span
          className="text-sm font-bold capitalize"
          style={{ color: 'var(--text-primary)' }}
        >
          {name}
        </span>
        <span
          className="text-sm font-mono"
          style={{ color: 'var(--text-secondary)' }}
        >
          {current}/{max}
        </span>
      </div>
      <div
        className="h-4 rounded-full overflow-hidden"
        style={{ backgroundColor: 'var(--bg-input)' }}
      >
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        />
      </div>
    </div>
  )
}
