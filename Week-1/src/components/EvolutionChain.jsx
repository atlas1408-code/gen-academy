import { usePokemonSpecies, useEvolutionChain, usePokemon } from '../hooks/usePokemon'

function flattenChain(chain) {
  const stages = []
  function walk(node, stage) {
    stages.push({
      name: node.species.name,
      stage,
      trigger: node.evolution_details?.[0] || null,
    })
    for (const next of node.evolves_to) {
      walk(next, stage + 1)
    }
  }
  walk(chain, 0)
  return stages
}

function getTriggerLabel(trigger) {
  if (!trigger) return ''
  if (trigger.min_level) return `LV.${trigger.min_level}`
  if (trigger.item) return trigger.item.name.replace(/-/g, ' ').toUpperCase()
  if (trigger.min_happiness) return `HAPPY ${trigger.min_happiness}`
  if (trigger.trigger?.name === 'trade') return 'TRADE'
  return ''
}

function EvolutionStage({ name, isCurrent, onSelect }) {
  const { data: pokemon } = usePokemon(name)
  const sprite = pokemon?.sprites?.other?.['official-artwork']?.front_default
    || pokemon?.sprites?.front_default

  return (
    <button
      onClick={() => onSelect(name)}
      className="flex flex-col items-center gap-1 cursor-pointer transition-transform hover:scale-105"
      style={{ opacity: isCurrent ? 1 : 0.5 }}
    >
      <div
        className="w-14 h-14 flex items-center justify-center"
        style={{
          backgroundColor: 'var(--bg-input)',
          border: isCurrent
            ? '2px solid var(--accent)'
            : '1px var(--border-style) var(--border-color)',
          borderRadius: 'var(--radius)',
        }}
      >
        {sprite && (
          <img src={sprite} alt={name} className="w-10 h-10 object-contain" />
        )}
      </div>
      <span
        className="text-xs uppercase"
        style={{
          color: isCurrent ? 'var(--text-highlight)' : 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.7rem',
        }}
      >
        {name}
      </span>
    </button>
  )
}

export default function EvolutionChain({ pokemonName, onSelect }) {
  const { data: species } = usePokemonSpecies(pokemonName)
  const evoUrl = species?.evolution_chain?.url
  const { data: evoData } = useEvolutionChain(evoUrl)

  if (!evoData) return null

  const stages = flattenChain(evoData.chain)
  if (stages.length <= 1) return null

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
        Evolution Chain
      </h4>
      <div className="flex items-center justify-center gap-2 flex-wrap">
        {stages.map((stage, i) => (
          <div key={stage.name} className="flex items-center gap-2">
            {i > 0 && (
              <div className="flex flex-col items-center">
                <span
                  className="text-sm"
                  style={{
                    color: 'var(--text-muted)',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  &gt;&gt;
                </span>
                {getTriggerLabel(stage.trigger) && (
                  <span
                    className="text-xs"
                    style={{
                      color: 'var(--text-muted)',
                      fontFamily: 'var(--font-pixel)',
                      fontSize: '0.4rem',
                    }}
                  >
                    {getTriggerLabel(stage.trigger)}
                  </span>
                )}
              </div>
            )}
            <EvolutionStage
              name={stage.name}
              isCurrent={stage.name === pokemonName}
              onSelect={onSelect}
            />
          </div>
        ))}
      </div>
    </div>
  )
}
