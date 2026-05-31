import { motion } from 'framer-motion'

export default function WinnerOverlay({ winner, analysis }) {
  if (!winner) return null

  const artwork = winner.sprites?.other?.['official-artwork']?.front_default

  return (
    <motion.div
      className="rounded-xl p-6 text-center"
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '2px solid var(--success)',
        boxShadow: '0 0 30px rgba(34, 197, 94, 0.2)',
      }}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      {artwork && (
        <motion.img
          src={artwork}
          alt={winner.name}
          className="w-24 h-24 mx-auto mb-3 object-contain"
          initial={{ y: -20 }}
          animate={{ y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        />
      )}
      <h3
        className="text-2xl font-black uppercase mb-2 capitalize"
        style={{ color: 'var(--success)' }}
      >
        🏆 {winner.name} Wins!
      </h3>
      {analysis && (
        <p
          className="text-sm max-w-lg mx-auto"
          style={{ color: 'var(--text-secondary)' }}
        >
          {analysis}
        </p>
      )}
    </motion.div>
  )
}
