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
      <h2
        className="mb-3 uppercase tracking-[0.2em]"
        style={{
          color: 'var(--text-highlight)',
          fontFamily: 'var(--font-pixel)',
          fontSize: '0.5rem',
        }}
      >
        Pokemon Database
      </h2>

      <div className="max-w-md mb-5">
        <SearchAutocomplete onSelect={setSelectedName} />
      </div>

      {!pokemon && !isLoading && !isError && (
        <div className="empty-state">
          <div className="empty-state__icon">?</div>
          <p className="empty-state__text">
            Enter a name to scan
            <span className="empty-state__cursor" />
          </p>
        </div>
      )}

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
