/**
 * Build a type chart from PokeAPI type data responses.
 * Returns a Map where each key is an attacking type name,
 * and the value contains sets of types it's super/not-very/immune against.
 */
export function buildTypeChart(typeDataArray) {
  const chart = new Map()
  for (const typeData of typeDataArray) {
    const name = typeData.name
    const relations = typeData.damage_relations
    chart.set(name, {
      doubleTo: new Set(relations.double_damage_to.map((t) => t.name)),
      halfTo: new Set(relations.half_damage_to.map((t) => t.name)),
      immuneTo: new Set(relations.no_damage_to.map((t) => t.name)),
    })
  }
  return chart
}

/**
 * Calculate the type effectiveness multiplier for an attack.
 * Multiplies across all defender types (supports dual-type: 4x, 0.25x, 0x).
 *
 * @param {string} attackType - The elemental type of the move
 * @param {string[]} defenderTypes - The defender's type(s)
 * @param {Map} typeChart - Built via buildTypeChart()
 * @returns {number} Multiplier (0, 0.25, 0.5, 1, 2, or 4)
 */
export function getEffectiveness(attackType, defenderTypes, typeChart) {
  const entry = typeChart.get(attackType)
  if (!entry) return 1

  let multiplier = 1
  for (const defType of defenderTypes) {
    if (entry.immuneTo.has(defType)) return 0
    if (entry.doubleTo.has(defType)) multiplier *= 2
    else if (entry.halfTo.has(defType)) multiplier *= 0.5
  }
  return multiplier
}
