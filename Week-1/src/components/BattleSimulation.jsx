import { useState, useEffect, useRef, useCallback } from 'react'
import { simulateBattle, selectTopMoves } from '../engine/battleEngine'
import { buildTypeChart } from '../utils/typeEffectiveness'
import { useAllTypes, useMoves } from '../hooks/usePokemon'
import HealthBar from './HealthBar'
import CombatLog from './CombatLog'
import WinnerOverlay from './WinnerOverlay'

export default function BattleSimulation({ pokemon1, pokemon2 }) {
  const [battleState, setBattleState] = useState(null)
  const [visibleEvents, setVisibleEvents] = useState([])
  const [currentHp1, setCurrentHp1] = useState(0)
  const [currentHp2, setCurrentHp2] = useState(0)
  const [isRunning, setIsRunning] = useState(false)
  const [isDone, setIsDone] = useState(false)
  const timerRef = useRef(null)

  const typeQueries = useAllTypes()
  const typesLoaded = typeQueries.every((q) => q.isSuccess)
  const typeChart = typesLoaded ? buildTypeChart(typeQueries.map((q) => q.data)) : null

  // Get moves for both pokemon
  const moveNames1 = pokemon1?.moves
    ?.filter((m) => m.version_group_details.some((d) => d.move_learn_method.name === 'level-up'))
    .map((m) => m.move.name) || []
  const moveNames2 = pokemon2?.moves
    ?.filter((m) => m.version_group_details.some((d) => d.move_learn_method.name === 'level-up'))
    .map((m) => m.move.name) || []

  const moveQueries1 = useMoves(moveNames1)
  const moveQueries2 = useMoves(moveNames2)

  const moves1Data = moveQueries1.filter((q) => q.isSuccess).map((q) => q.data)
  const moves2Data = moveQueries2.filter((q) => q.isSuccess).map((q) => q.data)

  const movesLoading = moveQueries1.some((q) => q.isLoading) || moveQueries2.some((q) => q.isLoading)

  const runBattle = useCallback(() => {
    if (!pokemon1 || !pokemon2 || !typeChart) return

    const top1 = selectTopMoves(moves1Data)
    const top2 = selectTopMoves(moves2Data)

    if (top1.length === 0 || top2.length === 0) return

    const result = simulateBattle(pokemon1, pokemon2, top1, top2, typeChart)
    setBattleState(result)
    setVisibleEvents([])
    setCurrentHp1(result.hp1Max)
    setCurrentHp2(result.hp2Max)
    setIsRunning(true)
    setIsDone(false)

    // Playback events with timed intervals
    let idx = 0
    if (timerRef.current) clearInterval(timerRef.current)

    timerRef.current = setInterval(() => {
      if (idx >= result.events.length) {
        clearInterval(timerRef.current)
        setIsRunning(false)
        setIsDone(true)
        return
      }

      const event = result.events[idx]
      setVisibleEvents((prev) => [...prev, event])

      if (event.type === 'attack') {
        setCurrentHp1(event.hp1)
        setCurrentHp2(event.hp2)
      }

      idx++
    }, 500)
  }, [pokemon1, pokemon2, typeChart, moves1Data, moves2Data])

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  const canRun = pokemon1 && pokemon2 && typeChart && !movesLoading
    && selectTopMoves(moves1Data).length > 0
    && selectTopMoves(moves2Data).length > 0

  const resultEvent = visibleEvents.find((e) => e.type === 'result')

  return (
    <div className="mt-8 space-y-4">
      <div className="flex justify-center">
        <button
          onClick={runBattle}
          disabled={!canRun || isRunning}
          className="px-8 py-3 rounded-lg text-sm font-bold uppercase tracking-wider transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          style={{
            backgroundColor: canRun && !isRunning ? 'var(--accent)' : 'var(--bg-input)',
            color: '#fff',
            boxShadow: canRun && !isRunning ? '0 0 20px var(--accent-glow)' : 'none',
          }}
        >
          {isRunning ? 'Simulating...' : movesLoading ? 'Loading moves...' : '⚔ Run Simulation'}
        </button>
      </div>

      {battleState && (
        <>
          <div className="flex gap-4">
            <HealthBar
              name={pokemon1.name}
              current={currentHp1}
              max={battleState.hp1Max}
            />
            <HealthBar
              name={pokemon2.name}
              current={currentHp2}
              max={battleState.hp2Max}
            />
          </div>

          <CombatLog events={visibleEvents} />

          {isDone && resultEvent && (
            <WinnerOverlay
              winner={battleState.winner}
              analysis={resultEvent.analysis}
            />
          )}
        </>
      )}
    </div>
  )
}
