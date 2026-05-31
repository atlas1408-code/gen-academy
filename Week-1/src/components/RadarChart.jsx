import { Radar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const STAT_KEYS = ['hp', 'attack', 'defense', 'special-attack', 'special-defense', 'speed']
const STAT_LABELS = ['HP', 'ATK', 'DEF', 'SPA', 'SPD', 'SPE']

function extractStats(pokemon) {
  return STAT_KEYS.map(
    (key) => pokemon.stats.find((s) => s.stat.name === key)?.base_stat || 0
  )
}

export default function RadarChart({ pokemon1, pokemon2 }) {
  if (!pokemon1 || !pokemon2) return null

  const data = {
    labels: STAT_LABELS,
    datasets: [
      {
        label: pokemon1.name,
        data: extractStats(pokemon1),
        backgroundColor: 'rgba(99, 179, 237, 0.25)',
        borderColor: 'rgba(99, 179, 237, 0.9)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(99, 179, 237, 1)',
        pointRadius: 4,
      },
      {
        label: pokemon2.name,
        data: extractStats(pokemon2),
        backgroundColor: 'rgba(237, 137, 54, 0.25)',
        borderColor: 'rgba(237, 137, 54, 0.9)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(237, 137, 54, 1)',
        pointRadius: 4,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#94a3b8',
          font: { size: 12 },
          usePointStyle: true,
          pointStyle: 'rectRounded',
        },
      },
    },
    scales: {
      r: {
        min: 0,
        max: 255,
        ticks: {
          stepSize: 50,
          display: false,
        },
        grid: {
          color: 'rgba(45, 34, 85, 0.6)',
        },
        angleLines: {
          color: 'rgba(45, 34, 85, 0.6)',
        },
        pointLabels: {
          color: '#94a3b8',
          font: { size: 12, weight: 'bold' },
        },
      },
    },
  }

  return (
    <div
      className="rounded-xl p-4"
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px var(--border-style) var(--border-color)',
      }}
    >
      <Radar data={data} options={options} />
    </div>
  )
}
