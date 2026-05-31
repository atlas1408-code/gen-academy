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
    <div
      className="rounded-xl p-5"
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px var(--border-style) var(--border-color)',
        boxShadow: 'var(--shadow)',
      }}
    >
      {artwork && (
        <div className={`flex justify-center mb-4 ${showPlatform ? 'battle-platform pb-3' : ''}`}>
          <img
            src={artwork}
            alt={pokemon.name}
            className={`${compact ? 'w-32 h-32' : 'w-48 h-48'} object-contain drop-shadow-lg`}
          />
        </div>
      )}

      <h3
        className="text-xl font-bold capitalize text-center mb-0.5"
        style={{ color: 'var(--text-primary)' }}
      >
        {pokemon.name}
      </h3>
      <p
        className="text-xs text-center mb-1"
        style={{ color: 'var(--text-muted)' }}
      >
        #{String(pokemon.id).padStart(3, '0')}
      </p>
      {genus && (
        <p
          className="text-xs text-center italic mb-3"
          style={{ color: 'var(--text-secondary)' }}
        >
          {genus}
        </p>
      )}

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

      {!compact && (
        <>
          {/* Height / Weight */}
          <div
            className="flex justify-center gap-6 mb-4 text-xs"
            style={{ color: 'var(--text-secondary)' }}
          >
            <div className="text-center">
              <span className="block font-bold" style={{ color: 'var(--text-primary)' }}>
                {heightM} m
              </span>
              Height
            </div>
            <div
              className="w-px"
              style={{ backgroundColor: 'var(--border-color)' }}
            />
            <div className="text-center">
              <span className="block font-bold" style={{ color: 'var(--text-primary)' }}>
                {weightKg} kg
              </span>
              Weight
            </div>
          </div>

          {/* Flavor Text */}
          {flavorText && (
            <p
              className="text-xs italic mb-4 text-center leading-relaxed px-2"
              style={{ color: 'var(--text-secondary)' }}
            >
              "{flavorText}"
            </p>
          )}

          {/* Abilities */}
          {abilities.length > 0 && (
            <div className="mb-4">
              <h4
                className="text-xs font-bold uppercase tracking-wider mb-2"
                style={{ color: 'var(--text-secondary)' }}
              >
                Abilities
              </h4>
              <div className="space-y-1.5">
                {abilities.map((ability) => (
                  <div
                    key={ability.name}
                    className="rounded-lg px-3 py-2"
                    style={{ backgroundColor: 'var(--bg-input)' }}
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="text-xs font-semibold capitalize"
                        style={{ color: 'var(--text-primary)' }}
                      >
                        {ability.name.replace(/-/g, ' ')}
                      </span>
                      {ability.isHidden && (
                        <span
                          className="text-xs px-1.5 py-0.5 rounded"
                          style={{
                            backgroundColor: 'var(--accent)',
                            color: '#fff',
                            fontSize: '0.6rem',
                          }}
                        >
                          HIDDEN
                        </span>
                      )}
                    </div>
                    {ability.shortEffect && (
                      <p
                        className="text-xs mt-0.5 leading-snug"
                        style={{ color: 'var(--text-muted)' }}
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

      <StatBarChart stats={stats} />
    </div>
  )
}
