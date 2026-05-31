import { useMoves } from '../hooks/usePokemon'
import { getTypeColor } from '../utils/typeColors'

export default function MovesGrid({ pokemon }) {
  if (!pokemon) return null

  const levelUpMoves = pokemon.moves
    .filter((m) =>
      m.version_group_details.some((d) => d.move_learn_method.name === 'level-up')
    )
    .map((m) => m.move.name)

  const moveQueries = useMoves(levelUpMoves)

  const loadedMoves = moveQueries
    .filter((q) => q.isSuccess && q.data.power !== null)
    .map((q) => q.data)
    .sort((a, b) => (b.power || 0) - (a.power || 0))

  const loading = moveQueries.some((q) => q.isLoading)

  return (
    <div>
      <h4
        className="text-sm font-bold uppercase tracking-wider mb-3"
        style={{ color: 'var(--text-secondary)' }}
      >
        Moves ({loadedMoves.length})
        {loading && <span className="ml-2 text-xs" style={{ color: 'var(--text-muted)' }}>loading...</span>}
      </h4>

      {loadedMoves.length === 0 && !loading && (
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          No powered moves found.
        </p>
      )}

      <div className="grid grid-cols-1 gap-1.5 max-h-96 overflow-y-auto pr-1">
        {loadedMoves.map((move) => (
          <div
            key={move.name}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm"
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px var(--border-style) var(--border-color)',
            }}
          >
            <span
              className="capitalize font-medium flex-1"
              style={{ color: 'var(--text-primary)' }}
            >
              {move.name.replace(/-/g, ' ')}
            </span>
            <span
              className="px-2 py-0.5 rounded text-xs font-semibold uppercase text-white"
              style={{ backgroundColor: getTypeColor(move.type.name) }}
            >
              {move.type.name}
            </span>
            <span
              className="text-xs w-12 text-center capitalize"
              style={{ color: 'var(--text-muted)' }}
            >
              {move.damage_class.name}
            </span>
            <span
              className="text-xs w-8 text-right font-mono"
              style={{ color: 'var(--text-primary)' }}
            >
              {move.power}
            </span>
            <span
              className="text-xs w-10 text-right font-mono"
              style={{ color: 'var(--text-secondary)' }}
            >
              {move.accuracy ?? '—'}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
