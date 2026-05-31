const TYPE_COLORS = {
  normal: '#a8a878',
  fire: '#ff4422',
  water: '#3399ff',
  electric: '#ffcc33',
  grass: '#77cc55',
  ice: '#66ccff',
  fighting: '#bb5544',
  poison: '#aa5599',
  ground: '#ddbb55',
  flying: '#8899ff',
  psychic: '#ff5599',
  bug: '#aabb22',
  rock: '#bbaa66',
  ghost: '#6666bb',
  dragon: '#7733ff',
  dark: '#775544',
  steel: '#aaaabb',
  fairy: '#ee99ee',
}

export function getTypeColor(typeName) {
  return TYPE_COLORS[typeName] || '#888888'
}

export default TYPE_COLORS
