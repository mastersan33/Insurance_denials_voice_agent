import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Profile from './pages/Profile';
import CallQueue from './pages/CallQueue';
import LiveCalls from './pages/LiveCalls';
import CallDetails from './pages/CallDetails';
import TranscriptViewer from './pages/TranscriptViewer';
import Settings from './pages/Settings';
import BillingCases from './pages/BillingCases';
import BillingCaseDetail from './pages/BillingCaseDetail';
import NewBillingCase from './pages/NewBillingCase';
import { useAuthStore } from './store/authStore';
import { useThemeStore } from './store/themeStore';

function App() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const { theme, setTheme } = useThemeStore();

  // Apply theme on mount
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
        <Route path="/settings" element={<Settings />} />
        <Route path="/profile" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
