import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import CallQueue from './pages/CallQueue';
import LiveCalls from './pages/LiveCalls';
import CallDetails from './pages/CallDetails';
import TranscriptViewer from './pages/TranscriptViewer';
import Settings from './pages/Settings';
import { useAuthStore } from './store/authStore';

function App() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/call-queue" element={<CallQueue />} />
        <Route path="/live-calls" element={<LiveCalls />} />
        <Route path="/calls/:id" element={<CallDetails />} />
        <Route path="/transcripts/:id" element={<TranscriptViewer />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
