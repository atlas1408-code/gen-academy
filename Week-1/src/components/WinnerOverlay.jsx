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
            style={{ backgroundColor: 'rgba(0, 0, 0, 0.85)' }}
            onClick={onDismiss}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          />

          {/* Device-style modal */}
          <motion.div
            className="relative p-6 text-center max-w-sm w-full"
            style={{
              backgroundColor: 'var(--bg-primary)',
              border: '3px solid var(--shell-dark)',
              borderRadius: 'var(--radius)',
              boxShadow: '0 0 40px rgba(255, 203, 5, 0.15), inset 0 0 15px rgba(80, 200, 120, 0.05)',
            }}
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 10 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          >
            {/* Top accent bar */}
            <div
              className="absolute top-0 left-0 right-0 h-1"
              style={{ backgroundColor: 'var(--accent-yellow)' }}
            />

            <motion.div
              className="mb-3 uppercase tracking-[0.3em]"
              style={{
                color: 'var(--text-muted)',
                fontFamily: 'var(--font-pixel)',
                fontSize: '0.4rem',
              }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              BATTLE RESULT
            </motion.div>

            {artwork && (
              <motion.img
                src={artwork}
                alt={winner.name}
                className="w-32 h-32 mx-auto mb-3 object-contain"
                style={{ filter: 'drop-shadow(0 0 12px rgba(255, 203, 5, 0.2))' }}
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.4, delay: 0.3 }}
              />
            )}

            <motion.h3
              className="uppercase mb-2"
              style={{
                color: 'var(--accent-yellow)',
                fontFamily: 'var(--font-pixel)',
                fontSize: '0.7rem',
                lineHeight: '1.8',
              }}
              initial={{ y: 15, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.4, delay: 0.4 }}
            >
              {winner.name} WINS!
            </motion.h3>

            <motion.div
              className="w-12 h-0.5 mx-auto mb-3"
              style={{ backgroundColor: 'var(--accent)' }}
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 0.4, delay: 0.5 }}
            />

            {analysis && (
              <motion.p
                className="text-xs leading-relaxed mb-4"
                style={{
                  color: 'var(--text-secondary)',
                  fontFamily: 'var(--font-mono)',
                }}
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.4, delay: 0.6 }}
              >
                {analysis}
              </motion.p>
            )}

            <motion.button
              onClick={onDismiss}
              className="px-6 py-1.5 text-xs font-bold uppercase tracking-wider cursor-pointer transition-colors"
              style={{
                backgroundColor: 'var(--accent)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius)',
                fontFamily: 'var(--font-pixel)',
                fontSize: '0.45rem',
              }}
              initial={{ y: 8, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.3, delay: 0.7 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              DISMISS
            </motion.button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
