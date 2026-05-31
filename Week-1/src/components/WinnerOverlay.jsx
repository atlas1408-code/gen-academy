import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function WinnerOverlay({ winner, analysis, onDismiss }) {
  // Lock body scroll when modal is open
  useEffect(() => {
    if (winner) {
      document.body.style.overflow = 'hidden'
      return () => { document.body.style.overflow = '' }
    }
  }, [winner])

  // Dismiss on Escape
  useEffect(() => {
    if (!winner) return
    function handleKey(e) {
      if (e.key === 'Escape') onDismiss?.()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [winner, onDismiss])

  const artwork = winner?.sprites?.other?.['official-artwork']?.front_default

  return (
    <AnimatePresence>
      {winner && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0"
            style={{ backgroundColor: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(4px)' }}
            onClick={onDismiss}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          />

          {/* Modal */}
          <motion.div
            className="relative rounded-2xl p-8 text-center max-w-md w-full"
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '2px solid var(--success)',
              boxShadow: '0 0 60px rgba(34, 197, 94, 0.25), 0 0 120px rgba(34, 197, 94, 0.1)',
            }}
            initial={{ opacity: 0, scale: 0.7, y: 30 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          >
            {/* Victory badge */}
            <motion.div
              className="text-5xl mb-4"
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ duration: 0.6, delay: 0.2, type: 'spring', bounce: 0.5 }}
            >
              🏆
            </motion.div>

            {artwork && (
              <motion.img
                src={artwork}
                alt={winner.name}
                className="w-36 h-36 mx-auto mb-4 object-contain"
                style={{ filter: 'drop-shadow(0 0 20px rgba(34, 197, 94, 0.3))' }}
                initial={{ y: 30, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.3 }}
              />
            )}

            <motion.h3
              className="text-3xl font-black uppercase mb-1 capitalize"
              style={{ color: 'var(--success)' }}
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.4, delay: 0.4 }}
            >
              {winner.name} Wins!
            </motion.h3>

            <motion.div
              className="w-16 h-0.5 mx-auto mb-4"
              style={{ backgroundColor: 'var(--success)' }}
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 0.4, delay: 0.5 }}
            />

            {analysis && (
              <motion.p
                className="text-sm leading-relaxed mb-6"
                style={{ color: 'var(--text-secondary)' }}
                initial={{ y: 15, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.4, delay: 0.6 }}
              >
                {analysis}
              </motion.p>
            )}

            <motion.button
              onClick={onDismiss}
              className="px-6 py-2 rounded-lg text-sm font-semibold cursor-pointer transition-colors"
              style={{
                backgroundColor: 'var(--accent)',
                color: '#fff',
              }}
              initial={{ y: 10, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.3, delay: 0.7 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Close
            </motion.button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
