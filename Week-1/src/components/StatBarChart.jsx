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
    <div className="space-y-1">
      {stats.map((stat) => (
        <div key={stat.name} className="stat-row">
          <span className="stat-label">
            {STAT_LABELS[stat.name] || stat.name}
          </span>
          <div className="stat-track">
            <div
              className="stat-fill"
              style={{
                width: `${(stat.value / MAX_STAT) * 100}%`,
                backgroundColor: STAT_COLORS[stat.name] || 'var(--accent)',
              }}
            />
          </div>
          <span className="stat-value">{stat.value}</span>
        </div>
      ))}
    </div>
  )
}
