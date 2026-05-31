import { NavLink, Routes, Route, Navigate } from 'react-router-dom'
import Explorer from './pages/Explorer'
import BattleArena from './pages/BattleArena'
import ThemeToggle from './components/ThemeToggle'

function App() {
  return (
    <div className="pokedex-shell">
      {/* ── Device Header: Lens + LEDs ── */}
      <div className="pokedex-header">
        <div className="pokedex-lens" />
        <div className="pokedex-leds">
          <div className="pokedex-led pokedex-led--red" />
          <div className="pokedex-led pokedex-led--yellow" />
          <div className="pokedex-led pokedex-led--green" />
        </div>
        <div className="ml-auto flex items-center gap-3">
          <ThemeToggle />
        </div>
      </div>

      {/* ── Main Screen ── */}
      <div className="pokedex-screen">
        {/* Screen header bar */}
        <div className="screen-header">
          <div>
            <span className="screen-header__title">
              <span style={{ color: 'var(--accent)' }}>Poke</span>Arena
            </span>
            <span className="screen-header__subtitle ml-2">Analytics v1.0</span>
          </div>
          <div className="power-indicator">
            <span>PWR</span>
            <div className="power-bar">
              <div className="power-bar__segment" />
              <div className="power-bar__segment" />
              <div className="power-bar__segment" />
              <div className="power-bar__segment power-bar__segment--empty" />
            </div>
          </div>
        </div>

        {/* Page content */}
        <div className="p-4">
          <Routes>
            <Route path="/explorer" element={<Explorer />} />
            <Route path="/battle" element={<BattleArena />} />
            <Route path="*" element={<Navigate to="/explorer" replace />} />
          </Routes>
        </div>
      </div>

      {/* ── Bottom bar: Nav + decorative controls ── */}
      <div className="pokedex-footer">
        {/* D-pad (decorative, compact) */}
        <div className="dpad dpad--small">
          <div className="dpad__horizontal" />
          <div className="dpad__vertical" />
        </div>

        {/* Navigation */}
        <div className="pokedex-nav">
          <NavLink
            to="/explorer"
            className={({ isActive }) =>
              `pokedex-nav__btn ${isActive ? 'pokedex-nav__btn--active' : ''}`
            }
          >
            Explorer
          </NavLink>
          <NavLink
            to="/battle"
            className={({ isActive }) =>
              `pokedex-nav__btn ${isActive ? 'pokedex-nav__btn--active' : ''}`
            }
          >
            Battle
          </NavLink>
        </div>

        {/* A/B buttons (decorative, compact) */}
        <div className="ab-buttons">
          <div className="ab-btn ab-btn--b">B</div>
          <div className="ab-btn ab-btn--a">A</div>
        </div>
      </div>
    </div>
  )
}

export default App
