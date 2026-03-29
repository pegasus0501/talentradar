/**
 * App.jsx — Root router.
 *
 * Two pages:
 *   /          → Home (prompt input)
 *   /results   → Results (top-5 candidates)
 *
 * We pass search results through router state so the Results page
 * doesn't need a separate API call — the data is already there.
 */
import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Results from './pages/Results'

export default function App() {
    return (
        <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/results" element={<Results />} />
        </Routes>
    )
}
