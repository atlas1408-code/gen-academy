import { useRef, useEffect } from 'react'

export default function CombatLog({ events }) {
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [events.length])

  return (
    <div
      className="rounded-xl p-4"
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px var(--border-style) var(--border-color)',
      }}
    >
      <h4
        className="text-xs font-bold uppercase tracking-wider mb-3"
        style={{ color: 'var(--text-secondary)' }}
      >
        Combat Log
      </h4>
      <div
        ref={scrollRef}
        className="max-h-64 overflow-y-auto space-y-1 text-sm font-mono"
      >
        {events.map((event, i) => {
          let style = { color: 'var(--text-secondary)' }
          if (event.type === 'initiative') style = { color: 'var(--warning)' }
          if (event.type === 'turn') style = { color: 'var(--text-muted)' }
          if (event.type === 'attack' && event.effectiveness >= 2) style = { color: 'var(--danger)' }
          if (event.type === 'miss') style = { color: 'var(--text-muted)', fontStyle: 'italic' }
          if (event.type === 'result') style = { color: 'var(--success)', fontWeight: 'bold' }

          return (
            <div key={i} style={style}>
              {event.type === 'turn' ? (
                <span>— Turn {event.turn} —</span>
              ) : event.type === 'initiative' ? (
                <span>⚡ {event.message}</span>
              ) : (
                <span>{event.message}</span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
