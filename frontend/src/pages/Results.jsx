/**
 * pages/Results.jsx — Top-5 candidate results page.
 *
 * Receives data via router state (set by Home.jsx after API call).
 * If no state (e.g. direct navigation), redirects to home.
 *
 * Layout sections:
 *   1. Navbar (with "New Search" button)
 *   2. Query summary bar — shows the parsed requirements
 *   3. AgentStatus panel — 3 agent status cards
 *   4. TopFiveGrid — ranked candidate cards
 *   5. Footer stats (total evaluated, time taken)
 */
import { useLocation, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import AgentStatus from '../components/AgentStatus'
import TopFiveGrid from '../components/TopFiveGrid'

export default function Results() {
    const { state } = useLocation()
    const navigate = useNavigate()

    useEffect(() => {
        if (!state?.data) navigate('/')
    }, [state, navigate])

    if (!state?.data) return null

    const { data, prompt } = state
    const {
        parsed_requirements: req,
        top_candidates,
        agent_statuses,
        total_candidates_evaluated,
        duration_ms,
        query_id,
    } = data

    return (
        <div style={{ position: 'relative', minHeight: '100vh' }}>
            <div className="bg-grid" />
            <div className="bg-glow" />

            {/* ── Navbar ── */}
            <nav style={styles.nav}>
                <div className="container" style={styles.navInner}>
                    <button
                        id="btn-logo-home"
                        onClick={() => navigate('/')}
                        style={styles.logoBtn}
                    >
                        <span>🎯</span>
                        <span style={styles.logoText}>TalentRadar</span>
                    </button>
                    <button
                        id="btn-new-search"
                        className="btn btn-ghost"
                        onClick={() => navigate('/')}
                        style={{ fontSize: '13px', padding: '8px 18px' }}
                    >
                        ← New Search
                    </button>
                </div>
            </nav>

            <main className="container" style={styles.main}>

                {/* ── Query summary ── */}
                <div className="glass fade-in" style={styles.queryCard}>
                    <div style={styles.queryLeft}>
                        <span style={styles.queryIcon}>🔍</span>
                        <div>
                            <p style={styles.queryLabel}>Search Query</p>
                            <p style={styles.queryText}>"{prompt}"</p>
                        </div>
                    </div>
                    <div style={styles.queryPills}>
                        {req.role && <span className="chip chip-default">{req.role}</span>}
                        {req.location && <span className="chip chip-cyan">📍 {req.location}</span>}
                        {req.years_exp_min > 0 && (
                            <span className="chip chip-green">⏱ {req.years_exp_min}+ yrs</span>
                        )}
                        {req.skills?.slice(0, 3).map(s => (
                            <span key={s} className="chip chip-default">{s}</span>
                        ))}
                    </div>
                </div>

                {/* ── Agent Status ── */}
                <div style={styles.sectionHeader}>
                    <h2 style={styles.sectionTitle}>
                        <span className="gradient-text">Agent Results</span>
                    </h2>
                    <p style={styles.sectionSub}>
                        {total_candidates_evaluated} candidates evaluated in {(duration_ms / 1000).toFixed(1)}s · Query #{query_id}
                    </p>
                </div>

                <AgentStatus statuses={agent_statuses} />

                {/* ── Top 5 ── */}
                <div style={{ ...styles.sectionHeader, marginTop: '48px' }}>
                    <h2 style={styles.sectionTitle}>
                        🏆 <span className="gradient-text">Top 5 Matches</span>
                    </h2>
                    <p style={styles.sectionSub}>Ranked by Gemini based on your requirements</p>
                </div>

                <TopFiveGrid candidates={top_candidates} requirements={req} />

            </main>
        </div>
    )
}

const styles = {
    nav: {
        position: 'relative',
        zIndex: 10,
        padding: '18px 0',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        backdropFilter: 'blur(20px)',
    },
    navInner: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    logoBtn: {
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        fontSize: '20px',
    },
    logoText: {
        fontFamily: "'Space Grotesk', sans-serif",
        fontSize: '20px',
        fontWeight: '700',
        background: 'linear-gradient(135deg, #a855f7, #06b6d4)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
    },
    main: {
        position: 'relative',
        zIndex: 1,
        paddingTop: '48px',
        paddingBottom: '80px',
    },
    queryCard: {
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px',
        padding: '20px 24px',
        marginBottom: '40px',
        animation: 'fadeIn 0.4s ease',
    },
    queryLeft: {
        display: 'flex',
        alignItems: 'flex-start',
        gap: '14px',
    },
    queryIcon: { fontSize: '22px', marginTop: '2px' },
    queryLabel: {
        fontSize: '11px',
        color: 'rgba(255,255,255,0.35)',
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
        marginBottom: '4px',
    },
    queryText: {
        fontSize: '15px',
        color: 'rgba(255,255,255,0.7)',
        fontStyle: 'italic',
        maxWidth: '500px',
    },
    queryPills: {
        display: 'flex',
        flexWrap: 'wrap',
        gap: '6px',
        alignItems: 'center',
    },
    sectionHeader: {
        marginBottom: '20px',
    },
    sectionTitle: {
        fontSize: '22px',
        fontWeight: '700',
        letterSpacing: '-0.02em',
        marginBottom: '4px',
    },
    sectionSub: {
        fontSize: '13px',
        color: 'rgba(255,255,255,0.35)',
    },
}
