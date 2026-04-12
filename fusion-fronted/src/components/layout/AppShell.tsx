import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'

export function AppShell() {
  return (
    <div className="flex min-h-screen bg-terminal-bg">
      <Sidebar />
      <main className="flex-1 flex flex-col min-w-0">
        <Outlet />
      </main>
    </div>
  )
}
