import { getTypeColor } from '../utils/typeColors'
import { usePokemonSpecies, useAbilities } from '../hooks/usePokemon'
import StatBarChart from './StatBarChart'

export default function PokemonCard({ pokemon, compact = false, showPlatform = false }) {
  if (!pokemon) return null

  const artwork = pokemon.sprites?.other?.['official-artwork']?.front_default
  const types = pokemon.types.map((t) => t.type.name)
  const stats = pokemon.stats.map((s) => ({
    name: s.stat.name,
    value: s.base_stat,
  }))

  const abilityNames = pokemon.abilities?.map((a) => a.ability.name) || []
  const hiddenFlags = pokemon.abilities?.map((a) => a.is_hidden) || []
  const { data: species } = usePokemonSpecies(pokemon.name)
  const abilityQueries = useAbilities(abilityNames)

  const genus = species?.genera?.find((g) => g.language.name === 'en')?.genus
  const flavorEntry = species?.flavor_text_entries?.find(
    (e) => e.language.name === 'en'
  )
  const flavorText = flavorEntry?.flavor_text?.replace(/[\f\n\r]/g, ' ')
  const heightM = (pokemon.height / 10).toFixed(1)
  const weightKg = (pokemon.weight / 10).toFixed(1)

  const abilities = abilityQueries
    .filter((q) => q.isSuccess)
    .map((q, i) => {
      const effect = q.data.effect_entries?.find((e) => e.language.name === 'en')
      return {
        name: q.data.name,
        shortEffect: effect?.short_effect || '',
        isHidden: hiddenFlags[i] || false,
      }
    })

  return (
    <div className="data-panel">
      {/* Scan-readout layout: sprite left, data right */}
      <div className={`flex ${compact ? 'flex-col items-center' : 'gap-4'}`}>
        {artwork && (
          <div className={`flex-shrink-0 flex justify-center ${showPlatform ? 'battle-platform pb-2' : ''}`}>
            <img
              src={artwork}
              alt={pokemon.name}
              className={`${compact ? 'w-28 h-28' : 'w-36 h-36'} object-contain`}
              style={{ filter: 'drop-shadow(0 0 6px rgba(80, 200, 120, 0.15))' }}
            />
          </div>
        )}

        <div className={`flex-1 ${compact ? 'text-center' : ''}`}>
          {/* Name + ID header */}
          <div className={`flex items-baseline gap-2 mb-1 ${compact ? 'justify-center' : ''}`}>
            <h3
              className="text-lg font-bold uppercase"
              style={{ color: 'var(--text-highlight)', fontFamily: 'var(--font-mono)' }}
            >
              {pokemon.name}
            </h3>
            <span
              className="text-xs"
              style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
            >
              #{String(pokemon.id).padStart(3, '0')}
            </span>
          </div>

          {genus && (
            <p
              className="text-xs mb-2"
              style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}
            >
              {genus}
            </p>
          )}

          {/* Type badges */}
          <div className={`flex gap-1.5 mb-3 ${compact ? 'justify-center' : ''}`}>
            {types.map((type) => (
              <span
                key={type}
                className="px-2 py-0.5 text-xs font-bold uppercase tracking-wider text-white"
                style={{
                  backgroundColor: getTypeColor(type),
                  borderRadius: 'var(--radius)',
                }}
              >
                {type}
              </span>
            ))}
          </div>

          {!compact && (
            <>
              {/* Height / Weight — inline data readout */}
              <div
                className="flex gap-4 mb-3 text-xs"
                style={{ fontFamily: 'var(--font-mono)' }}
              >
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>HT </span>
                  <span style={{ color: 'var(--text-primary)' }}>{heightM}m</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>WT </span>
                  <span style={{ color: 'var(--text-primary)' }}>{weightKg}kg</span>
                </div>
              </div>

              {/* Flavor Text */}
              {flavorText && (
                <p
                  className="text-xs mb-3 leading-relaxed"
                  style={{
                    color: 'var(--text-secondary)',
                    fontFamily: 'var(--font-mono)',
                    borderLeft: '2px solid var(--border-color)',
                    paddingLeft: '8px',
                  }}
                >
                  {flavorText}
                </p>
              )}

              {/* Abilities */}
              {abilities.length > 0 && (
                <div className="mb-3">
                  <h4
                    className="text-xs font-bold uppercase tracking-wider mb-1.5"
                    style={{
                      color: 'var(--text-secondary)',
                      fontFamily: 'var(--font-pixel)',
                      fontSize: '0.45rem',
                    }}
                  >
                    Abilities
                  </h4>
                  <div className="space-y-1">
                    {abilities.map((ability) => (
                      <div
                        key={ability.name}
                        className="px-2 py-1.5"
                        style={{
                          backgroundColor: 'var(--bg-input)',
                          borderRadius: 'var(--radius)',
                        }}
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className="text-xs font-bold uppercase"
                            style={{
                              color: 'var(--text-primary)',
                              fontFamily: 'var(--font-mono)',
                            }}
                          >
                            {ability.name.replace(/-/g, ' ')}
                          </span>
                          {ability.isHidden && (
                            <span
                              className="text-xs px-1 py-0.5"
                              style={{
                                backgroundColor: 'var(--accent)',
                                color: '#fff',
                                fontSize: '0.55rem',
                                fontFamily: 'var(--font-pixel)',
                                borderRadius: 'var(--radius)',
                              }}
                            >
                              HIDDEN
                            </span>
                          )}
                        </div>
                        {ability.shortEffect && (
                          <p
                            className="text-xs mt-0.5 leading-snug"
                            style={{
                              color: 'var(--text-muted)',
                              fontFamily: 'var(--font-mono)',
                            }}
                          >
                            {ability.shortEffect}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Stats always at bottom */}
      <div className="mt-3">
        <StatBarChart stats={stats} />
      </div>
    </div>
  )
}
