import { useState } from 'react'
import { usePokemon } from '../hooks/usePokemon'
import SearchAutocomplete from '../components/SearchAutocomplete'
import PokemonCard from '../components/PokemonCard'
import MovesGrid from '../components/MovesGrid'
import EvolutionChain from '../components/EvolutionChain'
import { CardSkeleton } from '../components/LoadingSkeleton'

export default function Explorer() {
  const [selectedName, setSelectedName] = useState('')
  const { data: pokemon, isLoading, isError } = usePokemon(selectedName)

  return (
    <div>
      <div className="screen-divider mb-4" />

      <h2
        className="mb-4 uppercase tracking-[0.2em]"
        style={{
          color: 'var(--text-highlight)',
          fontFamily: 'var(--font-pixel)',
          fontSize: '0.55rem',
        }}
      >
        Pokemon Database
      </h2>

      <div className="max-w-md mb-6">
        <SearchAutocomplete onSelect={setSelectedName} />
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      )}

      {isError && (
        <div className="data-panel text-center">
          <p
            className="text-sm uppercase"
            style={{
              color: 'var(--danger)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            ERROR: Failed to load Pokemon data. Check name and retry.
          </p>
        </div>
      )}

      {pokemon && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <PokemonCard pokemon={pokemon} />
            <MovesGrid pokemon={pokemon} />
          </div>
          <EvolutionChain
            pokemonName={pokemon.name}
            onSelect={setSelectedName}
          />
        </div>
      )}
    </div>
  )
}
