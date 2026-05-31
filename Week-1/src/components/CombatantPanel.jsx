import SearchAutocomplete from './SearchAutocomplete'
import { getTypeColor } from '../utils/typeColors'

const QUICK_PICKS = [
  'pikachu', 'charizard', 'blastoise', 'gengar', 'mewtwo', 'machamp',
  'garchomp', 'lucario',
]

const DRAFT_TYPES = [
  'fire', 'water', 'grass', 'electric', 'psychic', 'dragon',
  'ghost', 'fighting', 'steel', 'fairy',
]

export default function CombatantPanel({ label, selected, onSelect, onRandomDraft }) {
  return (
    <div className="data-panel flex-1">
      <h3
        className="mb-3 uppercase tracking-[0.15em]"
        style={{
          color: 'var(--text-highlight)',
          fontFamily: 'var(--font-pixel)',
          fontSize: '0.45rem',
        }}
      >
        {label}
      </h3>

      <SearchAutocomplete onSelect={onSelect} placeholder="SEARCH..." />

      {/* Quick picks */}
      <div className="flex flex-wrap gap-1 mt-3">
        {QUICK_PICKS.map((name) => (
          <button
            key={name}
            onClick={() => onSelect(name)}
            className="px-2 py-0.5 text-xs uppercase cursor-pointer transition-colors"
            style={{
              backgroundColor: selected === name ? 'var(--accent)' : 'var(--bg-input)',
              color: selected === name ? '#fff' : 'var(--text-secondary)',
              border: '1px var(--border-style) var(--border-color)',
              borderRadius: 'var(--radius)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.7rem',
            }}
          >
            {name}
          </button>
        ))}
      </div>

      {/* Type draft */}
      <div className="flex flex-wrap gap-1 mt-2">
        {DRAFT_TYPES.map((type) => (
          <button
            key={type}
            onClick={() => onRandomDraft(type)}
            className="px-1.5 py-0.5 text-xs uppercase cursor-pointer font-bold text-white"
            style={{
              backgroundColor: getTypeColor(type),
              borderRadius: 'var(--radius)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.65rem',
            }}
            title={`Random ${type}-type`}
          >
            {type}
          </button>
        ))}
      </div>
    </div>
  )
}
