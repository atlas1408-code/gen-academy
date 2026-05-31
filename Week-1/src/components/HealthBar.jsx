import { motion } from 'framer-motion'

export default function HealthBar({ name, current, max }) {
  const pct = Math.max(0, (current / max) * 100)
  const color = pct > 50 ? 'var(--success)' : pct > 20 ? 'var(--warning)' : 'var(--danger)'

  return (
    <div
      className="p-2"
      style={{
        backgroundColor: 'var(--bg-secondary)',
        border: '1px var(--border-style) var(--border-color)',
        borderRadius: 'var(--radius)',
      }}
    >
      <div className="flex justify-between mb-1">
        <span
          className="text-xs font-bold uppercase"
          style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}
        >
          {name}
        </span>
        <span
          className="text-xs"
          style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}
        >
          {current}/{max}
        </span>
      </div>
      <div
        className="h-3 overflow-hidden"
        style={{
          backgroundColor: 'var(--bg-input)',
          borderRadius: 'var(--radius)',
        }}
      >
        <motion.div
          className="h-full"
          style={{ backgroundColor: color, borderRadius: 'var(--radius)' }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        />
      </div>
    </div>
  )
}
