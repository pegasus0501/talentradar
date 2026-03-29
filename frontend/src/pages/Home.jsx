/**
 * pages/Home.jsx — Recruiter prompt entry page.
 *
 * Layout:
 *   - Fixed animated background (grid + glow)
 *   - Navbar with TalentRadar logo
 *   - Hero section: tagline + animated example prompt cycling
 *   - PromptInput card: textarea, example chips, submit button
 *   - Stats bar: database sizes
 *
 * On submit:
 *   Calls POST /api/search, shows a loading state, then navigates
 *   to /results passing the full API response via router state.
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import PromptInput from '../components/PromptInput'

const EXAMPLE_PROMPTS = [
    'Software engineer focused on distributed systems, 3+ years, AI/ML background, San Francisco',
    'Senior ML engineer with LLM fine-tuning experience, Python + PyTorch, any location',
    'Staff backend engineer with Kafka and Kubernetes expertise, 7+ years, remote ok',
    'Full stack engineer with React and Go, startup experience preferred, NYC or SF',
    'Principal engineer in platform/infrastructure, ex-FAANG, 10+ years experience',
]

export default function Home() {
    const navigate = useNavigate()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [currentExample, setCurrentExample] = useState(0)

    // Auto-cycle the example prompts in the hero
    useEffect(() => {
        const t = setInterval(
            () => setCurrentExample(i => (i + 1) % EXAMPLE_PROMPTS.length),
            3200,
        )
        return () => clearInterval(t)
    }, [])

    const handleSearch = async (prompt) => {
        setLoading(true)
        setError(null)
        try {
            const { data } = await axios.post('/api/search', { prompt })
            navigate('/results', { state: { data, prompt } })
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                'Search failed. Make sure the backend is running and API keys are configured.',
            )
            setLoading(false)
        }
    }

    return (
        <div style={{ position: 'relative', minHeight: '100vh' }}>
            {/* Ambient background */}
            <div className="bg-grid" />
            <div className="bg-glow" />

            {/* ── Navbar ── */}
            <nav style={styles.nav}>
                <div className="container" style={styles.navInner}>
                    <div style={styles.logo}>
                        <span style={styles.logoIcon}>🎯</span>
                        <span style={styles.logoText}>TalentRadar</span>
                    </div>
                    <div style={styles.navBadge}>Powered by Gemini + HydraDB</div>
                </div>
            </nav>

            {/* ── Hero ── */}
            <main className="container" style={styles.main}>
                <div style={styles.hero}>
                    <div style={styles.pillBadge}>
                        <span style={styles.pillDot} />
                        Multi-Agent AI Search
                    </div>

                    <h1 style={styles.heroTitle}>
                        Find your next{' '}
                        <span className="gradient-text">10× engineer</span>
                        <br />in seconds, not weeks.
                    </h1>

                    <p style={styles.heroSub}>
                        Describe your ideal candidate in plain English. Our AI searches your internal
                        database, LinkedIn, and GitHub simultaneously, then ranks the top 5 matches.
                    </p>

                    {/* Animated example prompt */}
                    <div style={styles.exampleWrap}>
                        <span style={styles.exampleLabel}>Try: </span>
                        <span
                            key={currentExample}
                            style={styles.exampleText}
                        >
                            "{EXAMPLE_PROMPTS[currentExample]}"
                        </span>
                    </div>
                </div>

                {/* ── Search Card ── */}
                <PromptInput
                    onSearch={handleSearch}
                    loading={loading}
                    examples={EXAMPLE_PROMPTS}
                />

                {/* ── Error ── */}
                {error && (
                    <div style={styles.errorBox}>
                        <span>⚠️</span> {error}
                    </div>
                )}

                {/* ── Stats bar ── */}
                <div style={styles.statsBar}>
                    {[
                        { label: 'Internal Profiles', value: '100+', icon: '🗃️' },
                        { label: 'LinkedIn Profiles', value: '40+', icon: '💼' },
                        { label: 'GitHub Devs', value: 'Live Search', icon: '🐙' },
                        { label: 'AI Model', value: 'Gemini 1.5 Pro', icon: '✨' },
                    ].map(s => (
                        <div key={s.label} className="glass" style={styles.statCard}>
                            <span style={styles.statIcon}>{s.icon}</span>
                            <span style={styles.statValue}>{s.value}</span>
                            <span style={styles.statLabel}>{s.label}</span>
                        </div>
                    ))}
                </div>
            </main>
        </div>
    )
}

/* ── Inline styles ──────────────────────────────────────────── */
const styles = {
    nav: {
        position: 'relative',
        zIndex: 10,
        paddingTop: '20px',
        paddingBottom: '20px',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        backdropFilter: 'blur(20px)',
    },
    navInner: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    logo: {
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
    },
    logoIcon: { fontSize: '24px' },
    logoText: {
        fontFamily: "'Space Grotesk', sans-serif",
        fontSize: '20px',
        fontWeight: '700',
        background: 'linear-gradient(135deg, #a855f7, #06b6d4)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
    },
    navBadge: {
        fontSize: '12px',
        color: 'rgba(255,255,255,0.4)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: '100px',
        padding: '4px 12px',
    },
    main: {
        position: 'relative',
        zIndex: 1,
        paddingTop: '80px',
        paddingBottom: '80px',
    },
    hero: {
        textAlign: 'center',
        marginBottom: '48px',
    },
    pillBadge: {
        display: 'inline-flex',
        alignItems: 'center',
        gap: '8px',
        background: 'rgba(124, 58, 237, 0.15)',
        border: '1px solid rgba(124, 58, 237, 0.3)',
        borderRadius: '100px',
        padding: '6px 16px',
        fontSize: '13px',
        color: '#a855f7',
        fontWeight: '500',
        marginBottom: '28px',
    },
    pillDot: {
        width: '7px',
        height: '7px',
        borderRadius: '50%',
        background: '#a855f7',
        boxShadow: '0 0 8px #a855f7',
        display: 'inline-block',
    },
    heroTitle: {
        fontSize: 'clamp(36px, 5vw, 62px)',
        fontWeight: '700',
        lineHeight: '1.15',
        marginBottom: '20px',
        letterSpacing: '-0.03em',
    },
    heroSub: {
        fontSize: '17px',
        color: 'rgba(255,255,255,0.55)',
        maxWidth: '540px',
        margin: '0 auto 28px',
        lineHeight: '1.7',
    },
    exampleWrap: {
        fontSize: '14px',
        color: 'rgba(255,255,255,0.4)',
        minHeight: '24px',
    },
    exampleLabel: { fontWeight: '600', color: 'rgba(255,255,255,0.5)' },
    exampleText: {
        color: 'rgba(168, 85, 247, 0.7)',
        fontStyle: 'italic',
        animation: 'fadeIn 0.4s ease',
    },
    errorBox: {
        marginTop: '16px',
        padding: '14px 20px',
        background: 'rgba(239, 68, 68, 0.1)',
        border: '1px solid rgba(239, 68, 68, 0.3)',
        borderRadius: '12px',
        color: '#fca5a5',
        fontSize: '14px',
        display: 'flex',
        gap: '10px',
    },
    statsBar: {
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '16px',
        marginTop: '64px',
    },
    statCard: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '6px',
        padding: '20px 16px',
        textAlign: 'center',
        transition: 'all 0.25s ease',
    },
    statIcon: { fontSize: '22px' },
    statValue: {
        fontFamily: "'Space Grotesk', sans-serif",
        fontWeight: '700',
        fontSize: '16px',
        color: '#f1f5f9',
    },
    statLabel: {
        fontSize: '12px',
        color: 'rgba(255,255,255,0.4)',
    },
}
