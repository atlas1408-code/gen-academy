import { motion } from 'framer-motion'

const STAT_LABELS = {
  hp: 'HP',
  attack: 'ATK',
  defense: 'DEF',
  'special-attack': 'SPA',
  'special-defense': 'SPD',
  speed: 'SPE',
}

const STAT_COLORS = {
  hp: '#ef4444',
  attack: '#f97316',
  defense: '#eab308',
  'special-attack': '#3b82f6',
  'special-defense': '#22c55e',
  speed: '#ec4899',
}

const MAX_STAT = 255

export default function StatBarChart({ stats }) {
  return (
    <div className="space-y-2">
      {stats.map((stat) => (
        <div key={stat.name} className="flex items-center gap-3">
          <span
            className="w-8 text-xs font-bold text-right"
            style={{ color: 'var(--text-secondary)' }}
          >
            {STAT_LABELS[stat.name] || stat.name}
          </span>
          <div
            className="flex-1 h-3 rounded-full overflow-hidden"
            style={{ backgroundColor: 'var(--bg-input)' }}
          >
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: STAT_COLORS[stat.name] || 'var(--accent)' }}
              initial={{ width: 0 }}
              animate={{ width: `${(stat.value / MAX_STAT) * 100}%` }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
            />
          </div>
          <span
            className="w-8 text-xs font-bold text-right"
            style={{ color: 'var(--text-primary)' }}
          >
            {stat.value}
          </span>
        </div>
      ))}
    </div>
  )
}
