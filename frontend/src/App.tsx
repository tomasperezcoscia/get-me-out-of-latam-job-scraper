import { Routes, Route } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import Dashboard from './pages/Dashboard'
import Jobs from './pages/Jobs'
import JobDetail from './pages/JobDetail'
import Applications from './pages/Applications'
import Sources from './pages/Sources'
import Profile from './pages/Profile'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/jobs" element={<Jobs />} />
        <Route path="/jobs/:id" element={<JobDetail />} />
        <Route path="/applications" element={<Applications />} />
        <Route path="/sources" element={<Sources />} />
        <Route path="/profile" element={<Profile />} />
      </Route>
    </Routes>
  )
}
