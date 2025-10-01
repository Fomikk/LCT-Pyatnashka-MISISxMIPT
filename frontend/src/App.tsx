import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import './App.css'
import SourcesPage from './pages/SourcesPage'
import PipelinePage from './pages/PipelinePage'
import JobsPage from './pages/JobsPage'
import AssistantPage from './pages/AssistantPage'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-neutral-50 text-neutral-900">
        <header className="border-b border-neutral-200 bg-white">
          <div className="mx-auto max-w-7xl px-6 py-3 flex items-center justify-between">
            <div className="text-lg font-semibold">ETL Assistant</div>
            <nav className="flex gap-2 text-sm">
              <NavItem to="/sources">Источники</NavItem>
              <NavItem to="/pipelines">Пайплайны</NavItem>
              <NavItem to="/jobs">Запуски</NavItem>
              <NavItem to="/assistant">Мастер</NavItem>
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-7xl px-6 py-8 min-h-[calc(100vh-57px)]">
          <Routes>
          <Route path="/" element={<Navigate to="/sources" replace />} />
          <Route path="/sources" element={<SourcesPage />} />
          <Route path="/pipelines" element={<PipelinePage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/assistant" element={<AssistantPage />} />
          <Route path="*" element={<div style={{ padding: 16 }}>Страница не найдена</div>} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App

function NavItem({ to, children }: { to: string; children: any }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `px-3 py-1 rounded-md transition-colors ${isActive ? 'bg-neutral-200 text-neutral-900' : 'text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100'}`
      }
    >
      {children}
    </NavLink>
  );
}
