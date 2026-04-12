import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/layout/ProtectedRoute'
import { AppShell } from './components/layout/AppShell'

import { LoginPage } from './pages/auth/LoginPage'
import { RegisterPage } from './pages/auth/RegisterPage'
import { VerifyEmailPage } from './pages/auth/VerifyEmailPage'
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage'
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage'
import { AnalysisPage } from './pages/AnalysisPage'
import { JournalPage } from './pages/JournalPage'
import { ModelsPage } from './pages/ModelsPage'
import { NewsletterPage } from './pages/NewsletterPage'
import { SettingsPage } from './pages/SettingsPage'
import { AboutPage } from './pages/AboutPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />

            {/* Protected routes */}
            <Route
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/analysis/GC%3DF" replace />} />
              <Route path="/analysis/:symbol" element={<AnalysisPage />} />
              <Route path="/journal" element={<JournalPage />} />
              <Route path="/models" element={<ModelsPage />} />
              <Route path="/newsletter" element={<NewsletterPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/about" element={<AboutPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
        <Toaster
          position="bottom-right"
          toastOptions={{
            style: {
              background: '#0d1526',
              color: '#e2e8f0',
              border: '1px solid #1a2840',
              fontSize: '13px',
            },
          }}
        />
      </AuthProvider>
    </QueryClientProvider>
  )
}
