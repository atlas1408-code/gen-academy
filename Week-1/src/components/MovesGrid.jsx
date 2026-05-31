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
    <div className="data-panel">
      <h4
        className="mb-3 uppercase tracking-[0.15em]"
        style={{
          color: 'var(--text-highlight)',
          fontFamily: 'var(--font-pixel)',
          fontSize: '0.5rem',
        }}
      >
        Moves ({loadedMoves.length})
        {loading && (
          <span className="ml-2" style={{ color: 'var(--text-muted)', fontSize: '0.45rem' }}>
            LOADING...
          </span>
        )}
      </h4>

      {loadedMoves.length === 0 && !loading && (
        <p
          className="text-sm uppercase"
          style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
        >
          No powered moves found.
        </p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 max-h-96 overflow-y-auto pr-1">
        {loadedMoves.map((move) => (
          <div
            key={move.name}
            className="flex items-center gap-2 px-2 py-1.5 text-xs"
            style={{
              backgroundColor: 'var(--bg-input)',
              borderRadius: 'var(--radius)',
              border: '1px var(--border-style) var(--border-color)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <span
              className="w-2 h-2 rounded-sm flex-shrink-0"
              style={{ backgroundColor: getTypeColor(move.type.name) }}
            />
            <span
              className="uppercase flex-1 truncate"
              style={{ color: 'var(--text-primary)' }}
            >
              {move.name.replace(/-/g, ' ')}
            </span>
            <span
              className="font-bold"
              style={{ color: 'var(--text-highlight)' }}
            >
              {move.power}
            </span>
            <span style={{ color: 'var(--text-muted)' }}>
              {move.accuracy ?? '—'}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
