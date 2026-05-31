import { getTypeColor } from '../utils/typeColors'
import StatBarChart from './StatBarChart'

export default function PokemonCard({ pokemon }) {
  if (!pokemon) return null

  const artwork = pokemon.sprites?.other?.['official-artwork']?.front_default
  const types = pokemon.types.map((t) => t.type.name)
  const stats = pokemon.stats.map((s) => ({
    name: s.stat.name,
    value: s.base_stat,
  }))

  return (
    <div
      className="rounded-xl p-5"
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px var(--border-style) var(--border-color)',
        boxShadow: 'var(--shadow)',
      }}
    >
      {artwork && (
        <div className="flex justify-center mb-4">
          <img
            src={artwork}
            alt={pokemon.name}
            className="w-48 h-48 object-contain drop-shadow-lg"
          />
        </div>
      )}

      <h3
        className="text-xl font-bold capitalize text-center mb-1"
        style={{ color: 'var(--text-primary)' }}
      >
        {pokemon.name}
      </h3>
      <p
        className="text-xs text-center mb-3"
        style={{ color: 'var(--text-muted)' }}
      >
        #{String(pokemon.id).padStart(3, '0')}
      </p>

      <div className="flex justify-center gap-2 mb-4">
        {types.map((type) => (
          <span
            key={type}
            className="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider text-white"
            style={{ backgroundColor: getTypeColor(type) }}
          >
            {type}
          </span>
        ))}
      </div>

      <StatBarChart stats={stats} />
    </div>
  )
}
