import { useState, useCallback } from 'react'
import { usePokemon, useTypeData } from '../hooks/usePokemon'
import CombatantPanel from '../components/CombatantPanel'
import PokemonCard from '../components/PokemonCard'
import RadarChart from '../components/RadarChart'
import BattleSimulation from '../components/BattleSimulation'

export default function BattleArena() {
  const [name1, setName1] = useState('')
  const [name2, setName2] = useState('')
  const [draftType1, setDraftType1] = useState(null)
  const [draftType2, setDraftType2] = useState(null)

  const { data: pokemon1, isLoading: loading1 } = usePokemon(name1)
  const { data: pokemon2, isLoading: loading2 } = usePokemon(name2)
  const { data: typeData1 } = useTypeData(draftType1)
  const { data: typeData2 } = useTypeData(draftType2)

  const handleRandomDraft = useCallback((type, setter, setDraftType) => {
    setDraftType(type)
  }, [])

  // When type data loads, pick random Pokémon from that type
  if (draftType1 && typeData1) {
    const list = typeData1.pokemon
    const pick = list[Math.floor(Math.random() * list.length)]
    setName1(pick.pokemon.name)
    setDraftType1(null)
  }
  if (draftType2 && typeData2) {
    const list = typeData2.pokemon
    const pick = list[Math.floor(Math.random() * list.length)]
    setName2(pick.pokemon.name)
    setDraftType2(null)
  }

  const bothSelected = pokemon1 && pokemon2

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
        Battle Arena
      </h2>

      {/* Selection panels */}
      <div className="flex flex-col md:flex-row items-stretch gap-3 mb-6">
        <CombatantPanel
          label="Combatant 1"
          selected={name1}
          onSelect={setName1}
          onRandomDraft={(type) => handleRandomDraft(type, setName1, setDraftType1)}
        />
        <div
          className="self-center uppercase tracking-wider"
          style={{
            color: 'var(--danger)',
            fontFamily: 'var(--font-pixel)',
            fontSize: '0.7rem',
          }}
        >
          VS
        </div>
        <CombatantPanel
          label="Combatant 2"
          selected={name2}
          onSelect={setName2}
          onRandomDraft={(type) => handleRandomDraft(type, setName2, setDraftType2)}
        />
      </div>

      {(loading1 || loading2) && (
        <p
          className="text-sm mb-4 uppercase"
          style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
        >
          Loading Pokemon data...
        </p>
      )}

      {/* Matchup analysis */}
      {bothSelected && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <PokemonCard pokemon={pokemon1} compact showPlatform />
            <RadarChart pokemon1={pokemon1} pokemon2={pokemon2} />
            <PokemonCard pokemon={pokemon2} compact showPlatform />
          </div>

          <BattleSimulation pokemon1={pokemon1} pokemon2={pokemon2} />
        </>
      )}
    </div>
  )
}
