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
  const [showWinner, setShowWinner] = useState(false)
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
    setShowWinner(false)

    // Playback events with timed intervals
    let idx = 0
    if (timerRef.current) clearInterval(timerRef.current)

    timerRef.current = setInterval(() => {
      if (idx >= result.events.length) {
        clearInterval(timerRef.current)
        setIsRunning(false)
        setTimeout(() => setShowWinner(true), 600)
        return
      }

      const event = result.events[idx]
      setVisibleEvents((prev) => [...prev, event])

      if (event.type === 'attack') {
        setCurrentHp1(event.hp1)
        setCurrentHp2(event.hp2)
      }

      idx++
    }, 1200)
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

  const resultEvent = battleState?.events?.find((e) => e.type === 'result')

  return (
    <div className="mt-6 space-y-4">
      <div className="flex justify-center">
        <button
          onClick={runBattle}
          disabled={!canRun || isRunning}
          className="px-8 py-2.5 text-xs font-bold uppercase tracking-[0.2em] cursor-pointer transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          style={{
            backgroundColor: canRun && !isRunning ? 'var(--accent)' : 'var(--bg-input)',
            color: '#fff',
            border: '2px solid',
            borderColor: canRun && !isRunning ? 'var(--accent)' : 'var(--border-color)',
            borderRadius: 'var(--radius)',
            fontFamily: 'var(--font-pixel)',
            fontSize: '0.55rem',
            boxShadow: canRun && !isRunning ? '0 0 15px var(--accent-glow)' : 'none',
          }}
        >
          {isRunning ? 'SIMULATING...' : movesLoading ? 'LOADING MOVES...' : 'RUN SIMULATION'}
        </button>
      </div>

      {battleState && (
        <>
          {/* Battle stage */}
          <div className="data-panel">
            <div className="flex gap-4 items-end justify-center">
              {/* Combatant 1 */}
              <div className="flex-1 max-w-[200px]">
                <HealthBar
                  name={pokemon1.name}
                  current={currentHp1}
                  max={battleState.hp1Max}
                />
                <div className="flex justify-center mt-2 pb-2">
                  <img
                    src={pokemon1.sprites?.other?.['official-artwork']?.front_default}
                    alt={pokemon1.name}
                    className="w-24 h-24 object-contain"
                    style={{ filter: 'drop-shadow(0 0 6px rgba(80, 200, 120, 0.15))' }}
                  />
                </div>
              </div>

              {/* VS divider */}
              <div
                className="pb-6 uppercase"
                style={{
                  color: 'var(--accent-yellow)',
                  fontFamily: 'var(--font-pixel)',
                  fontSize: '0.7rem',
                }}
              >
                VS
              </div>

              {/* Combatant 2 */}
              <div className="flex-1 max-w-[200px]">
                <HealthBar
                  name={pokemon2.name}
                  current={currentHp2}
                  max={battleState.hp2Max}
                />
                <div className="flex justify-center mt-2 pb-2">
                  <img
                    src={pokemon2.sprites?.other?.['official-artwork']?.front_default}
                    alt={pokemon2.name}
                    className="w-24 h-24 object-contain"
                    style={{ filter: 'drop-shadow(0 0 6px rgba(80, 200, 120, 0.15))' }}
                  />
                </div>
              </div>
            </div>
          </div>

          <CombatLog events={visibleEvents} />
        </>
      )}

      <WinnerOverlay
        winner={showWinner ? battleState?.winner : null}
        analysis={resultEvent?.analysis}
        onDismiss={() => setShowWinner(false)}
      />
    </div>
  )
}
