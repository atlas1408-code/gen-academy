import { useState, useRef, useEffect } from 'react'
import { usePokemonList } from '../hooks/usePokemon'

export default function SearchAutocomplete({ onSelect, placeholder = 'SEARCH POKEMON...' }) {
  const [query, setQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [highlightIndex, setHighlightIndex] = useState(-1)
  const { data: allNames = [] } = usePokemonList()
  const wrapperRef = useRef(null)
  const listRef = useRef(null)

  const filtered = query.length >= 1
    ? allNames.filter((name) => name.startsWith(query.toLowerCase())).slice(0, 20)
    : []

  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    if (highlightIndex >= 0 && listRef.current) {
      const el = listRef.current.children[highlightIndex]
      if (el) el.scrollIntoView({ block: 'nearest' })
    }
  }, [highlightIndex])

  function handleSelect(name) {
    setQuery('')
    setIsOpen(false)
    setHighlightIndex(-1)
    onSelect(name)
  }

  function handleKeyDown(e) {
    if (!isOpen || filtered.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlightIndex((i) => Math.min(i + 1, filtered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlightIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' && highlightIndex >= 0) {
      e.preventDefault()
      handleSelect(filtered[highlightIndex])
    } else if (e.key === 'Escape') {
      setIsOpen(false)
    }
  }

  return (
    <div ref={wrapperRef} className="relative w-full">
      <div
        className="flex items-center gap-2 px-3 py-2"
        style={{
          backgroundColor: 'var(--bg-input)',
          border: '2px var(--border-style) var(--border-color)',
          borderRadius: 'var(--radius)',
        }}
      >
        <span
          style={{
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.9rem',
            flexShrink: 0,
          }}
        >
          &gt;
        </span>
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setIsOpen(true)
            setHighlightIndex(-1)
          }}
          onFocus={() => query.length >= 1 && setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="w-full text-sm outline-none uppercase tracking-wider bg-transparent"
          style={{
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-mono)',
            caretColor: 'var(--success)',
          }}
        />
      </div>
      {isOpen && filtered.length > 0 && (
        <ul
          ref={listRef}
          className="absolute z-50 w-full mt-1 overflow-auto max-h-60"
          style={{
            backgroundColor: 'var(--bg-card)',
            border: '2px solid var(--border-color)',
            borderRadius: 'var(--radius)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
          }}
        >
          {filtered.map((name, i) => (
            <li
              key={name}
              onClick={() => handleSelect(name)}
              className="px-3 py-1.5 text-sm cursor-pointer uppercase tracking-wider"
              style={{
                backgroundColor: i === highlightIndex ? 'var(--bg-card-hover)' : 'transparent',
                color: i === highlightIndex ? 'var(--text-highlight)' : 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
              }}
              onMouseEnter={() => setHighlightIndex(i)}
            >
              {name}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
