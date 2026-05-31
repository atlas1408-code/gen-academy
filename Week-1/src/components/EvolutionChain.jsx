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
  if (trigger.min_level) return `Lv. ${trigger.min_level}`
  if (trigger.item) return trigger.item.name.replace(/-/g, ' ')
  if (trigger.min_happiness) return `Happiness ${trigger.min_happiness}`
  if (trigger.trigger?.name === 'trade') return 'Trade'
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
      style={{ opacity: isCurrent ? 1 : 0.6 }}
    >
      <div
        className="w-16 h-16 rounded-full flex items-center justify-center"
        style={{
          backgroundColor: 'var(--bg-input)',
          border: isCurrent
            ? '2px solid var(--accent)'
            : '1px var(--border-style) var(--border-color)',
        }}
      >
        {sprite && (
          <img src={sprite} alt={name} className="w-12 h-12 object-contain" />
        )}
      </div>
      <span
        className="text-xs capitalize font-medium"
        style={{ color: isCurrent ? 'var(--text-primary)' : 'var(--text-muted)' }}
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
    <div
      className="rounded-xl p-4"
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px var(--border-style) var(--border-color)',
        boxShadow: 'var(--shadow)',
      }}
    >
      <h4
        className="text-xs font-bold uppercase tracking-wider mb-4"
        style={{ color: 'var(--text-secondary)' }}
      >
        Evolution Chain
      </h4>
      <div className="flex items-center justify-center gap-2 flex-wrap">
        {stages.map((stage, i) => (
          <div key={stage.name} className="flex items-center gap-2">
            {i > 0 && (
              <div className="flex flex-col items-center">
                <span
                  className="text-lg"
                  style={{ color: 'var(--text-muted)' }}
                >
                  →
                </span>
                {getTriggerLabel(stage.trigger) && (
                  <span
                    className="text-xs"
                    style={{ color: 'var(--text-muted)' }}
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
