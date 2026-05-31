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
    <div
      className="rounded-xl p-4 flex-1"
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px var(--border-style) var(--border-color)',
      }}
    >
      <h3
        className="text-xs font-bold uppercase tracking-wider mb-3"
        style={{ color: 'var(--text-secondary)' }}
      >
        {label}
      </h3>

      <SearchAutocomplete onSelect={onSelect} placeholder="Search..." />

      <div className="flex flex-wrap gap-1.5 mt-3">
        {QUICK_PICKS.map((name) => (
          <button
            key={name}
            onClick={() => onSelect(name)}
            className="px-3 py-1 rounded-full text-xs capitalize transition-colors cursor-pointer"
            style={{
              backgroundColor: selected === name ? 'var(--accent)' : 'var(--bg-input)',
              color: selected === name ? '#fff' : 'var(--text-secondary)',
              border: '1px var(--border-style) var(--border-color)',
            }}
          >
            {name}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap gap-1.5 mt-3">
        {DRAFT_TYPES.map((type) => (
          <button
            key={type}
            onClick={() => onRandomDraft(type)}
            className="px-2 py-0.5 rounded text-xs capitalize cursor-pointer font-semibold text-white"
            style={{ backgroundColor: getTypeColor(type) }}
            title={`Random ${type}-type`}
          >
            {type}
          </button>
        ))}
      </div>
    </div>
  )
}
