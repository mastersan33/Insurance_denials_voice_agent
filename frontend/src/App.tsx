import { lazy, Suspense, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import { useAuthStore } from './store/authStore';
import { useThemeStore } from './store/themeStore';

// ── Eagerly loaded (critical auth path) ──────────────────────────────────
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';

// ── Lazy loaded (separate chunks) ────────────────────────────────────────
const Dashboard         = lazy(() => import('./pages/Dashboard'));
const BillingCases      = lazy(() => import('./pages/BillingCases'));
const NewBillingCase    = lazy(() => import('./pages/NewBillingCase'));
const BillingCaseDetail = lazy(() => import('./pages/BillingCaseDetail'));
const CallQueue         = lazy(() => import('./pages/CallQueue'));
const LiveCalls         = lazy(() => import('./pages/LiveCalls'));
const CallDetails       = lazy(() => import('./pages/CallDetails'));
const TranscriptViewer  = lazy(() => import('./pages/TranscriptViewer'));
const Analytics         = lazy(() => import('./pages/Analytics'));
const Reports           = lazy(() => import('./pages/Reports'));
const Tickets           = lazy(() => import('./pages/Tickets'));
const HumanHandoff      = lazy(() => import('./pages/HumanHandoff'));
const Users             = lazy(() => import('./pages/Users'));
const SystemHealth      = lazy(() => import('./pages/SystemHealth'));
const AuditLog          = lazy(() => import('./pages/AuditLog'));
const Settings          = lazy(() => import('./pages/Settings'));
const Profile           = lazy(() => import('./pages/Profile'));

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
    </div>
  );
}

function App() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const { theme, setTheme } = useThemeStore();

  useEffect(() => {
    setTheme(theme);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/billing-cases" element={<BillingCases />} />
          <Route path="/billing-cases/new" element={<NewBillingCase />} />
          <Route path="/billing-cases/:id" element={<BillingCaseDetail />} />
          <Route path="/call-queue" element={<CallQueue />} />
          <Route path="/live-calls" element={<LiveCalls />} />
          <Route path="/calls/:id" element={<CallDetails />} />
          <Route path="/transcripts/:id" element={<TranscriptViewer />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/tickets" element={<Tickets />} />
          <Route path="/human-handoff" element={<HumanHandoff />} />
          <Route path="/users" element={<Users />} />
          <Route path="/system-health" element={<SystemHealth />} />
          <Route path="/audit-log" element={<AuditLog />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/profile" element={<Profile />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

export default App;
