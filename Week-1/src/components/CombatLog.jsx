import { useRef, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getTypeColor } from '../utils/typeColors'

function TypewriterText({ text, speed = 20, onComplete }) {
  const [displayed, setDisplayed] = useState('')
  const indexRef = useRef(0)

  useEffect(() => {
    setDisplayed('')
    indexRef.current = 0
    const timer = setInterval(() => {
      indexRef.current++
      if (indexRef.current >= text.length) {
        setDisplayed(text)
        clearInterval(timer)
        onComplete?.()
      } else {
        setDisplayed(text.slice(0, indexRef.current + 1))
      }
    }, speed)
    return () => clearInterval(timer)
  }, [text, speed])

  return <span>{displayed}</span>
}

function MangaPanel({ event, isLatest }) {
  if (event.type === 'turn') {
    return (
      <motion.div
        className="relative my-4 py-2 text-center"
        initial={{ opacity: 0, scaleX: 0 }}
        animate={{ opacity: 1, scaleX: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div
          className="inline-block px-6 py-1 font-black text-lg uppercase tracking-[0.3em] skew-x-[-3deg]"
          style={{
            backgroundColor: 'var(--text-primary)',
            color: 'var(--bg-primary)',
            clipPath: 'polygon(4% 0%, 100% 0%, 96% 100%, 0% 100%)',
          }}
        >
          {event.narrative || `TURN ${event.turn}`}
        </div>
      </motion.div>
    )
  }

  if (event.type === 'initiative') {
    return (
      <motion.div
        className="relative my-3 p-4 rounded-lg text-center"
        style={{
          backgroundColor: 'var(--bg-secondary)',
          borderLeft: '4px solid var(--warning)',
        }}
        initial={{ opacity: 0, x: -30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.4 }}
      >
        <p
          className="text-sm font-semibold italic"
          style={{ color: 'var(--warning)' }}
        >
          {isLatest ? (
            <TypewriterText text={event.narrative} speed={25} />
          ) : (
            event.narrative
          )}
        </p>
      </motion.div>
    )
  }

  if (event.type === 'miss') {
    return (
      <motion.div
        className="relative my-2 p-3 rounded-lg"
        style={{
          backgroundColor: 'var(--bg-secondary)',
          borderLeft: '4px solid var(--text-muted)',
          opacity: 0.7,
        }}
        initial={{ opacity: 0, x: 20, rotate: 1 }}
        animate={{ opacity: 0.7, x: 0, rotate: 0 }}
        transition={{ duration: 0.3 }}
      >
        <p
          className="text-sm italic"
          style={{ color: 'var(--text-muted)' }}
        >
          {isLatest ? (
            <TypewriterText text={event.narrative} speed={20} />
          ) : (
            event.narrative
          )}
        </p>
      </motion.div>
    )
  }

  if (event.type === 'attack') {
    const narrativeLines = event.narrative || [event.message]
    const isBigHit = event.effectiveness >= 2
    const isDevastating = event.damage > 50
    const moveColor = getTypeColor(event.moveType)

    return (
      <motion.div
        className="relative my-2"
        initial={{ opacity: 0, y: 15 }}
        animate={{
          opacity: 1,
          y: 0,
          x: isBigHit ? [0, -3, 3, -2, 2, 0] : 0,
        }}
        transition={{
          duration: isBigHit ? 0.5 : 0.3,
          x: { duration: 0.4, ease: 'easeInOut' },
        }}
      >
        {/* Panel container */}
        <div
          className="rounded-lg overflow-hidden"
          style={{
            border: isBigHit
              ? `2px solid ${moveColor}`
              : '1px var(--border-style) var(--border-color)',
            boxShadow: isBigHit ? `0 0 15px ${moveColor}40` : 'none',
          }}
        >
          {/* Attacker banner */}
          <div
            className="px-3 py-1.5 flex items-center gap-2"
            style={{ backgroundColor: `${moveColor}20` }}
          >
            <span
              className="text-xs font-black uppercase tracking-wider capitalize"
              style={{ color: moveColor }}
            >
              {event.attacker}
            </span>
            <span
              className="px-2 py-0.5 rounded text-xs font-bold uppercase text-white"
              style={{ backgroundColor: moveColor }}
            >
              {event.move.replace(/-/g, ' ')}
            </span>
            {isBigHit && (
              <motion.span
                className="ml-auto text-xs font-black uppercase"
                style={{ color: 'var(--danger)' }}
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 0.3, repeat: 1 }}
              >
                {event.effectiveness >= 4 ? '4x!!' : 'SUPER EFFECTIVE!'}
              </motion.span>
            )}
          </div>

          {/* Narrative body */}
          <div
            className="px-3 py-2.5 space-y-1"
            style={{ backgroundColor: 'var(--bg-secondary)' }}
          >
            {narrativeLines.map((line, i) => (
              <p
                key={i}
                className={`text-sm leading-relaxed ${i === 0 ? 'font-semibold' : ''}`}
                style={{
                  color: i === narrativeLines.length - 1 && event.effectiveness >= 2
                    ? 'var(--danger)'
                    : 'var(--text-primary)',
                  fontStyle: i > 0 ? 'italic' : 'normal',
                }}
              >
                {isLatest && i === narrativeLines.length - 1 ? (
                  <TypewriterText text={line} speed={15} />
                ) : (
                  line
                )}
              </p>
            ))}
          </div>

          {/* Damage footer */}
          <div
            className="px-3 py-1.5 flex items-center justify-between"
            style={{
              backgroundColor: isDevastating ? `${moveColor}15` : 'var(--bg-card)',
              borderTop: '1px solid var(--border-color)',
            }}
          >
            <span
              className="text-xs font-mono"
              style={{ color: 'var(--text-muted)' }}
            >
              {event.effectivenessText || 'Normal effectiveness'}
            </span>
            <motion.span
              className="text-sm font-black font-mono"
              style={{ color: isDevastating ? 'var(--danger)' : 'var(--text-primary)' }}
              initial={isLatest ? { scale: 1.5 } : {}}
              animate={{ scale: 1 }}
              transition={{ duration: 0.3 }}
            >
              -{event.damage} HP
            </motion.span>
          </div>
        </div>
      </motion.div>
    )
  }

  // Fallback for result or unknown
  return null
}

export default function CombatLog({ events }) {
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [events.length])

  // Filter out result events (handled by WinnerOverlay)
  const displayEvents = events.filter((e) => e.type !== 'result')

  return (
    <div
      className="rounded-xl p-4"
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px var(--border-style) var(--border-color)',
      }}
    >
      <h4
        className="text-xs font-bold uppercase tracking-[0.2em] mb-3 flex items-center gap-2"
        style={{ color: 'var(--text-secondary)' }}
      >
        <span
          className="inline-block w-6 h-0.5"
          style={{ backgroundColor: 'var(--accent)' }}
        />
        Battle Chronicle
        <span
          className="inline-block w-6 h-0.5"
          style={{ backgroundColor: 'var(--accent)' }}
        />
      </h4>
      <div
        ref={scrollRef}
        className="max-h-[500px] overflow-y-auto pr-1"
      >
        <AnimatePresence>
          {displayEvents.map((event, i) => (
            <MangaPanel
              key={i}
              event={event}
              isLatest={i === displayEvents.length - 1}
            />
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
