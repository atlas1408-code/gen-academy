import { useState } from 'react'
import { usePokemon } from '../hooks/usePokemon'
import SearchAutocomplete from '../components/SearchAutocomplete'
import PokemonCard from '../components/PokemonCard'
import MovesGrid from '../components/MovesGrid'
import { CardSkeleton } from '../components/LoadingSkeleton'

export default function Explorer() {
  const [selectedName, setSelectedName] = useState('')
  const { data: pokemon, isLoading, isError } = usePokemon(selectedName)

  return (
    <div>
      <h2
        className="text-2xl font-bold mb-6"
        style={{ color: 'var(--text-primary)' }}
      >
        Single Search
      </h2>

      <div className="max-w-md mb-8">
        <SearchAutocomplete onSelect={setSelectedName} />
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      )}

      {isError && (
        <div
          className="rounded-xl p-6 text-center"
          style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--danger)',
          }}
        >
          <p className="text-sm" style={{ color: 'var(--danger)' }}>
            Failed to load Pokémon data. Please check the name and try again.
          </p>
        </div>
      )}

      {pokemon && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <PokemonCard pokemon={pokemon} />
          <MovesGrid pokemon={pokemon} />
        </div>
      )}
    </div>
  )
}
