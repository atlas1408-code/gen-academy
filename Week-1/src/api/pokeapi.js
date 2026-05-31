const BASE_URL = import.meta.env.VITE_POKEAPI_BASE_URL || 'https://pokeapi.co/api/v2'

async function fetchJson(url) {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`PokeAPI error: ${res.status} ${res.statusText}`)
  return res.json()
}

export function fetchPokemon(nameOrId) {
  return fetchJson(`${BASE_URL}/pokemon/${nameOrId}`)
}

export function fetchMove(nameOrId) {
  return fetchJson(`${BASE_URL}/move/${nameOrId}`)
}

export function fetchTypeData(type) {
  return fetchJson(`${BASE_URL}/type/${type}`)
}

export function fetchPokemonList(limit = 1302) {
  return fetchJson(`${BASE_URL}/pokemon?limit=${limit}&offset=0`)
}
