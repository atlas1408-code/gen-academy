/**
 * Manga-style battle narrator.
 * Generates dramatic, varied narrative lines for battle events.
 */

const ATTACK_OPENERS = [
  (a, m) => `${a} unleashes a devastating ${m}!`,
  (a, m) => `${a} strikes with ${m}!`,
  (a, m) => `With blazing fury, ${a} launches ${m}!`,
  (a, m) => `${a} channels its power... ${m}!`,
  (a, m) => `The air crackles as ${a} delivers ${m}!`,
  (a, m) => `${a} surges forward — ${m}!`,
  (a, m) => `In a flash, ${a} executes ${m}!`,
  (a, m) => `${a} roars and releases ${m}!`,
  (a, m) => `Without hesitation, ${a} goes for ${m}!`,
  (a, m) => `${a} gathers energy and fires off ${m}!`,
]

const DAMAGE_REACTIONS = {
  devastating: [
    (d, dmg) => `A crushing ${dmg} damage! ${d} staggers under the weight of the blow!`,
    (d, dmg) => `${dmg} damage tears through ${d}'s defenses! This could be the end!`,
    (d, dmg) => `An earth-shattering ${dmg} damage! ${d} is barely holding on!`,
  ],
  heavy: [
    (d, dmg) => `${dmg} damage rocks ${d} to its core!`,
    (d, dmg) => `A solid hit — ${dmg} damage! ${d} winces in pain!`,
    (d, dmg) => `${d} takes ${dmg} damage and skids backward!`,
  ],
  moderate: [
    (d, dmg) => `${dmg} damage connects cleanly!`,
    (d, dmg) => `The attack lands for ${dmg} damage. ${d} grits its teeth.`,
    (d, dmg) => `A steady ${dmg} damage. ${d} absorbs the impact.`,
  ],
  light: [
    (d, dmg) => `Only ${dmg} damage... ${d} barely flinches.`,
    (d, dmg) => `A glancing blow — ${dmg} damage. ${d} stands firm.`,
    (d, dmg) => `${dmg} damage. ${d} shrugs it off with ease.`,
  ],
}

const SUPER_EFFECTIVE = [
  "It's super effective! The type advantage is overwhelming!",
  "Super effective! The elemental weakness is exposed!",
  "A critical type matchup! Super effective damage!",
  "The attack exploits a devastating weakness!",
]

const QUAD_EFFECTIVE = [
  "QUADRUPLE DAMAGE! An absolutely catastrophic type matchup!",
  "4x effective! The double weakness is mercilessly exploited!",
  "A BRUTAL 4x hit! There's no surviving that kind of punishment!",
]

const NOT_EFFECTIVE = [
  "Not very effective... the attack barely scratches the surface.",
  "The type resistance absorbs most of the impact...",
  "A resisted hit — the damage is underwhelming.",
]

const MISS_LINES = [
  (a, m) => `${a} goes for ${m}... but it misses! The attack sails wide!`,
  (a, m) => `${a} launches ${m} — but ${m} finds only empty air!`,
  (a, m) => `A desperate ${m} from ${a}! ...But it whiffs completely!`,
  (a, m) => `${a} swings with ${m}! The opponent dodges at the last second!`,
  (a, m) => `${m} from ${a} — MISS! So close, yet so far!`,
]

const INITIATIVE_LINES = [
  (name, spd1, spd2) => `The battle begins! ${name} seizes the initiative with superior speed! (${spd1} vs ${spd2})`,
  (name, spd1, spd2) => `${name} moves first — its lightning reflexes give it the edge! (SPE: ${spd1} vs ${spd2})`,
  (name, spd1, spd2) => `With a speed stat of ${spd1} against ${spd2}, ${name} strikes first!`,
]

const TURN_OPENERS = [
  (n) => `ROUND ${n}`,
  (n) => `TURN ${n}`,
  (n) => `CHAPTER ${n}`,
]

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)]
}

function formatMoveName(name) {
  return name.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatPokemonName(name) {
  return name.charAt(0).toUpperCase() + name.slice(1)
}

export function narrateInitiative(firstName, speed1, speed2) {
  return pick(INITIATIVE_LINES)(formatPokemonName(firstName), speed1, speed2)
}

export function narrateTurn(turnNumber) {
  return pick(TURN_OPENERS)(turnNumber)
}

export function narrateAttack(attackerName, defenderName, moveName, damage, effectiveness, hpRemaining, hpMax) {
  const a = formatPokemonName(attackerName)
  const d = formatPokemonName(defenderName)
  const m = formatMoveName(moveName)

  const parts = []

  // Opening line
  parts.push(pick(ATTACK_OPENERS)(a, m))

  // Effectiveness callout
  if (effectiveness >= 4) {
    parts.push(pick(QUAD_EFFECTIVE))
  } else if (effectiveness >= 2) {
    parts.push(pick(SUPER_EFFECTIVE))
  } else if (effectiveness > 0 && effectiveness < 1) {
    parts.push(pick(NOT_EFFECTIVE))
  }

  // Damage reaction based on percentage of max HP
  const dmgPct = damage / hpMax
  let tier
  if (dmgPct > 0.4) tier = 'devastating'
  else if (dmgPct > 0.2) tier = 'heavy'
  else if (dmgPct > 0.1) tier = 'moderate'
  else tier = 'light'

  parts.push(pick(DAMAGE_REACTIONS[tier])(d, damage))

  // Low HP dramatic callout
  const hpPct = hpRemaining / hpMax
  if (hpPct > 0 && hpPct < 0.15) {
    parts.push(`${d} is hanging by a thread!`)
  } else if (hpPct === 0) {
    parts.push(`${d} collapses! It's unable to battle!`)
  }

  return parts
}

export function narrateMiss(attackerName, moveName) {
  return pick(MISS_LINES)(formatPokemonName(attackerName), formatMoveName(moveName))
}
