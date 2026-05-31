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
          className="inline-block px-6 py-1.5 uppercase tracking-[0.3em] skew-x-[-3deg]"
          style={{
            backgroundColor: 'var(--accent-yellow)',
            color: '#000',
            fontFamily: 'var(--font-pixel)',
            fontSize: '0.65rem',
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
        className="relative my-3 p-4 dialog-box"
        style={{
          backgroundColor: 'var(--bg-secondary)',
        }}
        initial={{ opacity: 0, x: -30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.4 }}
      >
        <p
          style={{
            color: 'var(--accent-yellow)',
            fontFamily: 'var(--font-retro)',
            fontSize: '1.1rem',
            lineHeight: '1.4',
          }}
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
        className="relative my-2 p-3 dialog-box"
        style={{
          backgroundColor: 'var(--bg-secondary)',
          opacity: 0.7,
        }}
        initial={{ opacity: 0, x: 20, rotate: 1 }}
        animate={{ opacity: 0.7, x: 0, rotate: 0 }}
        transition={{ duration: 0.3 }}
      >
        <p
          style={{
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-retro)',
            fontSize: '1.1rem',
            fontStyle: 'italic',
          }}
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
          x: isBigHit ? [0, -4, 4, -3, 3, -1, 0] : 0,
        }}
        transition={{
          duration: isBigHit ? 0.5 : 0.3,
          x: { duration: 0.4, ease: 'easeInOut' },
        }}
      >
        <div
          className="overflow-hidden"
          style={{
            border: isBigHit
              ? `3px double ${moveColor}`
              : '3px double var(--border-color)',
            borderRadius: '4px',
            boxShadow: isBigHit ? `0 0 20px ${moveColor}40` : 'none',
          }}
        >
          {/* Attacker banner */}
          <div
            className="px-3 py-1.5 flex items-center gap-2"
            style={{ backgroundColor: `${moveColor}20` }}
          >
            <span
              className="uppercase tracking-wider capitalize"
              style={{
                color: moveColor,
                fontFamily: 'var(--font-pixel)',
                fontSize: '0.55rem',
              }}
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
                className="ml-auto uppercase"
                style={{
                  color: 'var(--danger)',
                  fontFamily: 'var(--font-pixel)',
                  fontSize: '0.5rem',
                }}
                animate={{ scale: [1, 1.3, 1] }}
                transition={{ duration: 0.3, repeat: 2 }}
              >
                {event.effectiveness >= 4 ? '4x DAMAGE!!' : 'SUPER EFFECTIVE!'}
              </motion.span>
            )}
          </div>

          {/* Narrative body — retro text box */}
          <div
            className="px-3 py-3 space-y-1.5"
            style={{ backgroundColor: 'var(--bg-secondary)' }}
          >
            {narrativeLines.map((line, i) => (
              <p
                key={i}
                style={{
                  color: i === narrativeLines.length - 1 && event.effectiveness >= 2
                    ? 'var(--danger)'
                    : 'var(--text-primary)',
                  fontFamily: 'var(--font-retro)',
                  fontSize: '1.05rem',
                  lineHeight: '1.3',
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
              borderTop: '3px double var(--border-color)',
            }}
          >
            <span
              style={{
                color: 'var(--text-muted)',
                fontFamily: 'var(--font-retro)',
                fontSize: '0.95rem',
              }}
            >
              {event.effectivenessText || 'Normal effectiveness'}
            </span>
            <motion.span
              className="font-black"
              style={{
                color: isDevastating ? 'var(--danger)' : 'var(--accent-yellow)',
                fontFamily: 'var(--font-pixel)',
                fontSize: '0.6rem',
              }}
              initial={isLatest ? { scale: 1.8 } : {}}
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

  return null
}

export default function CombatLog({ events }) {
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [events.length])

  const displayEvents = events.filter((e) => e.type !== 'result')

  return (
    <div
      className="dialog-box p-4"
      style={{
        backgroundColor: 'var(--bg-card)',
      }}
    >
      <h4
        className="mb-3 flex items-center gap-2 uppercase tracking-[0.2em]"
        style={{
          color: 'var(--accent-yellow)',
          fontFamily: 'var(--font-pixel)',
          fontSize: '0.6rem',
        }}
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
