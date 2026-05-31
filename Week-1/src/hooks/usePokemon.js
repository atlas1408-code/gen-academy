import { useQuery, useQueries } from '@tanstack/react-query'
import {
  fetchPokemon, fetchMove, fetchTypeData, fetchPokemonList,
  fetchPokemonSpecies, fetchAbility, fetchEvolutionChain,
} from '../api/pokeapi'

export function usePokemon(name) {
  return useQuery({
    queryKey: ['pokemon', name],
    queryFn: () => fetchPokemon(name),
    enabled: !!name,
  })
}

export function usePokemonList() {
  return useQuery({
    queryKey: ['pokemon-list'],
    queryFn: () => fetchPokemonList(),
    select: (data) => data.results.map((p) => p.name),
  })
}

export function useMove(name) {
  return useQuery({
    queryKey: ['move', name],
    queryFn: () => fetchMove(name),
    enabled: !!name,
  })
}

export function useMoves(moveNames) {
  return useQueries({
    queries: (moveNames || []).map((name) => ({
      queryKey: ['move', name],
      queryFn: () => fetchMove(name),
      enabled: !!name,
    })),
  })
}

export function useTypeData(type) {
  return useQuery({
    queryKey: ['type', type],
    queryFn: () => fetchTypeData(type),
    enabled: !!type,
  })
}

const ALL_TYPES = [
  'normal', 'fire', 'water', 'electric', 'grass', 'ice',
  'fighting', 'poison', 'ground', 'flying', 'psychic', 'bug',
  'rock', 'ghost', 'dragon', 'dark', 'steel', 'fairy',
]

export function usePokemonSpecies(name) {
  return useQuery({
    queryKey: ['pokemon-species', name],
    queryFn: () => fetchPokemonSpecies(name),
    enabled: !!name,
  })
}

export function useAbilities(abilityNames) {
  return useQueries({
    queries: (abilityNames || []).map((name) => ({
      queryKey: ['ability', name],
      queryFn: () => fetchAbility(name),
      enabled: !!name,
    })),
  })
}

export function useEvolutionChain(url) {
  return useQuery({
    queryKey: ['evolution-chain', url],
    queryFn: () => fetchEvolutionChain(url),
    enabled: !!url,
  })
}

export function useAllTypes() {
  return useQueries({
    queries: ALL_TYPES.map((type) => ({
      queryKey: ['type', type],
      queryFn: () => fetchTypeData(type),
    })),
  })
}
