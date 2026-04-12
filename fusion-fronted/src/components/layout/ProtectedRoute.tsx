import { Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { SkeletonCard } from '../ui/Skeleton'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-terminal-bg p-8 space-y-4">
        <SkeletonCard lines={4} />
        <SkeletonCard lines={3} />
      </div>
    )
  }

  if (!token) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
