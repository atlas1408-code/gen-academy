import { getEffectiveness } from '../utils/typeEffectiveness'
import { narrateInitiative, narrateTurn, narrateAttack, narrateMiss } from '../utils/narrator'

/**
 * Calculate actual HP at level 50 (simplified formula).
 */
function calcHP(baseHP) {
  return baseHP * 2 + 110
}

/**
 * Pick the best move (highest expected damage) against the defender.
 */
function pickMove(moves, attacker, defender, typeChart) {
  let bestMove = moves[0]
  let bestDamage = 0

  for (const move of moves) {
    const dmg = calcDamage(move, attacker, defender, typeChart, 1) // variance=1 for estimation
    if (dmg > bestDamage) {
      bestDamage = dmg
      bestMove = move
    }
  }
  return bestMove
}

/**
 * Calculate damage for a single attack.
 */
function calcDamage(move, attacker, defender, typeChart, variance) {
  const attackerTypes = attacker.types.map((t) => t.type.name)
  const defenderTypes = defender.types.map((t) => t.type.name)

  const isPhysical = move.damage_class.name === 'physical'
  const atkStat = getStat(attacker, isPhysical ? 'attack' : 'special-attack')
  const defStat = getStat(defender, isPhysical ? 'defense' : 'special-defense')

  const typeMult = typeChart
    ? getEffectiveness(move.type.name, defenderTypes, typeChart)
    : 1
  const stab = attackerTypes.includes(move.type.name) ? 1.5 : 1

  const baseDamage = (move.power * atkStat) / (defStat * 8) + 2
  return Math.floor(baseDamage * typeMult * stab * variance)
}

function getStat(pokemon, statName) {
  return pokemon.stats.find((s) => s.stat.name === statName)?.base_stat || 50
}

/**
 * Simulate a full battle between two Pokémon.
 * Returns { events, winner, turns, analysis }.
 */
export function simulateBattle(pokemon1, pokemon2, moves1, moves2, typeChart) {
  const hp1Max = calcHP(getStat(pokemon1, 'hp'))
  const hp2Max = calcHP(getStat(pokemon2, 'hp'))
  let hp1 = hp1Max
  let hp2 = hp2Max

  const speed1 = getStat(pokemon1, 'speed')
  const speed2 = getStat(pokemon2, 'speed')

  const first = speed1 > speed2 ? 1 : speed1 < speed2 ? 2 : Math.random() < 0.5 ? 1 : 2

  const events = []
  let totalDmg1 = 0
  let totalDmg2 = 0
  let superEffectiveHits1 = 0
  let superEffectiveHits2 = 0

  const firstName = first === 1 ? pokemon1.name : pokemon2.name
  events.push({
    type: 'initiative',
    message: `${firstName} goes first! (SPE ${first === 1 ? speed1 : speed2} vs ${first === 1 ? speed2 : speed1})`,
    narrative: narrateInitiative(firstName, first === 1 ? speed1 : speed2, first === 1 ? speed2 : speed1),
  })

  let turn = 0
  const MAX_TURNS = 100

  while (hp1 > 0 && hp2 > 0 && turn < MAX_TURNS) {
    turn++
    events.push({ type: 'turn', turn, narrative: narrateTurn(turn) })

    const attackOrder = first === 1
      ? [
          { attacker: pokemon1, defender: pokemon2, moves: moves1, side: 1 },
          { attacker: pokemon2, defender: pokemon1, moves: moves2, side: 2 },
        ]
      : [
          { attacker: pokemon2, defender: pokemon1, moves: moves2, side: 2 },
          { attacker: pokemon1, defender: pokemon2, moves: moves1, side: 1 },
        ]

    for (const { attacker, defender, moves, side } of attackOrder) {
      if ((side === 1 && hp1 <= 0) || (side === 2 && hp2 <= 0)) break
      if ((side === 1 && hp2 <= 0) || (side === 2 && hp1 <= 0)) break

      const move = pickMove(moves, attacker, defender, typeChart)
      const accuracyRoll = Math.random() * 100

      if (move.accuracy !== null && accuracyRoll > move.accuracy) {
        events.push({
          type: 'miss',
          attacker: attacker.name,
          move: move.name,
          message: `${attacker.name} used ${move.name.replace(/-/g, ' ')} — but it missed!`,
          narrative: narrateMiss(attacker.name, move.name),
        })
        continue
      }

      const variance = 0.85 + Math.random() * 0.15
      const damage = calcDamage(move, attacker, defender, typeChart, variance)
      const defenderTypes = defender.types.map((t) => t.type.name)
      const effectiveness = typeChart
        ? getEffectiveness(move.type.name, defenderTypes, typeChart)
        : 1

      if (side === 1) {
        hp2 = Math.max(0, hp2 - damage)
        totalDmg1 += damage
        if (effectiveness > 1) superEffectiveHits1++
      } else {
        hp1 = Math.max(0, hp1 - damage)
        totalDmg2 += damage
        if (effectiveness > 1) superEffectiveHits2++
      }

      let effectivenessText = ''
      if (effectiveness >= 4) effectivenessText = 'Super effective! (4x)'
      else if (effectiveness >= 2) effectivenessText = 'Super effective!'
      else if (effectiveness === 0) effectivenessText = 'No effect!'
      else if (effectiveness < 1) effectivenessText = 'Not very effective...'

      const defHpRemaining = side === 1 ? hp2 : hp1
      const defHpMax = side === 1 ? hp2Max : hp1Max

      events.push({
        type: 'attack',
        attacker: attacker.name,
        defender: defender.name,
        move: move.name,
        moveType: move.type.name,
        damage,
        effectiveness,
        effectivenessText,
        hp1,
        hp2,
        hp1Max,
        hp2Max,
        message: `${attacker.name} → ${move.name.replace(/-/g, ' ')} (${damage} dmg)${effectivenessText ? ' ' + effectivenessText : ''}`,
        narrative: narrateAttack(attacker.name, defender.name, move.name, damage, effectiveness, defHpRemaining, defHpMax),
      })
    }
  }

  const winner = hp1 > 0 ? pokemon1 : pokemon2
  const loser = hp1 > 0 ? pokemon2 : pokemon1

  const analysis = generateInsight(
    winner, loser, turn, speed1, speed2,
    hp1 > 0 ? totalDmg1 : totalDmg2,
    hp1 > 0 ? superEffectiveHits1 : superEffectiveHits2,
    hp1 > 0 ? getStat(winner, 'defense') : getStat(winner, 'defense'),
  )

  events.push({
    type: 'result',
    winner: winner.name,
    message: `${winner.name} wins!`,
    analysis,
  })

  return { events, winner, loser, turns: turn, hp1, hp2, hp1Max, hp2Max }
}

function generateInsight(winner, loser, turns, speed1, speed2, totalDmg, superHits, winnerDef) {
  const winnerSpeed = getStat(winner, 'speed')
  const loserSpeed = getStat(loser, 'speed')

  if (superHits >= 2) {
    return `${winner.name} capitalized on type-effectiveness, landing ${superHits} super-effective hits to overcome ${loser.name}.`
  }
  if (winnerSpeed > loserSpeed * 1.3) {
    return `${winner.name}'s massive Speed advantage (${winnerSpeed} vs ${loserSpeed}) allowed it to strike first and secure the knockout.`
  }
  if (winnerDef >= 120 && turns >= 6) {
    return `${winner.name}'s towering Defense (${winnerDef}) neutralized ${loser.name}'s attacks, wearing it down over ${turns} turn${turns === 1 ? '' : 's'}.`
  }
  if (turns <= 3) {
    return `${winner.name} closed out the match with overwhelming offensive pressure, finishing ${loser.name} in just ${turns} turn${turns === 1 ? '' : 's'}.`
  }
  return `${winner.name} outlasted ${loser.name} in a hard-fought ${turns}-turn battle, dealing ${totalDmg} total damage.`
}

/**
 * Select the top N powered moves for a Pokémon.
 */
export function selectTopMoves(moveDataArray, count = 4) {
  return moveDataArray
    .filter((m) => m && m.power !== null)
    .sort((a, b) => b.power - a.power)
    .slice(0, count)
}
