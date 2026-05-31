import { NavLink, Routes, Route, Navigate } from 'react-router-dom'
import Explorer from './pages/Explorer'
import BattleArena from './pages/BattleArena'
import ThemeToggle from './components/ThemeToggle'

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header
        className="flex items-center justify-between px-6 py-3 border-b"
        style={{
          backgroundColor: 'var(--bg-secondary)',
          borderColor: 'var(--border-color)',
        }}
      >
        <div className="flex items-center gap-6">
          <h1
            className="text-lg font-bold tracking-tight"
            style={{ color: 'var(--accent)' }}
          >
            PokeArena Analytics
          </h1>
          <nav className="flex gap-2">
            <NavLink
              to="/explorer"
              className={({ isActive }) =>
                `px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  isActive
                    ? 'text-white'
                    : 'hover:opacity-80'
                }`
              }
              style={({ isActive }) => ({
                backgroundColor: isActive ? 'var(--accent)' : 'transparent',
                color: isActive ? '#fff' : 'var(--text-secondary)',
                border: isActive ? 'none' : '1px solid var(--border-color)',
              })}
            >
              Single Search
            </NavLink>
            <NavLink
              to="/battle"
              className={({ isActive }) =>
                `px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  isActive
                    ? 'text-white'
                    : 'hover:opacity-80'
                }`
              }
              style={({ isActive }) => ({
                backgroundColor: isActive ? 'var(--accent)' : 'transparent',
                color: isActive ? '#fff' : 'var(--text-secondary)',
                border: isActive ? 'none' : '1px solid var(--border-color)',
              })}
            >
              Battle Arena
            </NavLink>
          </nav>
        </div>
        <ThemeToggle />
      </header>

      <main className="flex-1 p-6">
        <Routes>
          <Route path="/explorer" element={<Explorer />} />
          <Route path="/battle" element={<BattleArena />} />
          <Route path="*" element={<Navigate to="/explorer" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
