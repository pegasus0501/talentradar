/**
 * components/CandidateCard.jsx
 *
 * A single ranked candidate card showing:
 *   - Rank badge (#1–#5) with coloured glow
 *   - Avatar (DiceBear SVG or initials fallback)
 *   - Name, title, company, location
 *   - Score ring (animated SVG circle progress) with score 0–100
 *   - Source badge (Internal DB / LinkedIn / GitHub)
 *   - Skill chips
 *   - AI explanation (from Gemini)
 *   - Strengths + Gaps accordion
 *   - Links to LinkedIn/GitHub profiles
 *
 * Props:
 *   candidate: ScoredCandidate (profile + score + explanation + rank)
 *   isTop:     boolean — rank === 1 (gets gold treatment)
 */
import { useState } from 'react'

const RANK_COLORS = {
    1: { bg: 'rgba(251,191,36,0.25)', border: 'rgba(251,191,36,0.5)', text: '#fbbf24', label: '🥇 #1' },
    2: { bg: 'rgba(148,163,184,0.15)', border: 'rgba(148,163,184,0.4)', text: '#94a3b8', label: '🥈 #2' },
    3: { bg: 'rgba(205,127,50,0.15)', border: 'rgba(205,127,50,0.4)', text: '#cd7f32', label: '🥉 #3' },
    4: { bg: 'rgba(124,58,237,0.12)', border: 'rgba(124,58,237,0.3)', text: '#a855f7', label: '#4' },
    5: { bg: 'rgba(124,58,237,0.08)', border: 'rgba(124,58,237,0.2)', text: '#7c3aed', label: '#5' },
}

const SOURCE_BADGES = {
    internal: { label: '🗃️ Internal DB', color: '#a855f7', bg: 'rgba(168,85,247,0.12)' },
    linkedin: { label: '💼 LinkedIn', color: '#10b981', bg: 'rgba(16,185,129,0.12)' },
    github: { label: '🐙 GitHub', color: '#06b6d4', bg: 'rgba(6,182,212,0.12)' },
}

function ScoreRing({ score }) {
    const R = 30
    const CIRC = 2 * Math.PI * R
    const filled = (score / 100) * CIRC
    const color = score >= 75 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444'

    return (
        <div style={{ position: 'relative', width: 76, height: 76, flexShrink: 0 }}>
            <svg width="76" height="76" style={{ transform: 'rotate(-90deg)' }}>
                <circle cx="38" cy="38" r={R} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6" />
                <circle
                    cx="38" cy="38" r={R}
                    fill="none"
                    stroke={color}
                    strokeWidth="6"
                    strokeLinecap="round"
                    strokeDasharray={CIRC}
                    strokeDashoffset={CIRC - filled}
                    style={{ transition: 'stroke-dashoffset 1s ease, stroke 0.3s ease', filter: `drop-shadow(0 0 6px ${color}80)` }}
                />
            </svg>
            <div style={{
                position: 'absolute', inset: 0, display: 'flex',
                flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            }}>
                <span style={{ fontFamily: "'Space Grotesk',sans-serif", fontWeight: '700', fontSize: '17px', color }}>{score}</span>
                <span style={{ fontSize: '9px', color: 'rgba(255,255,255,0.3)', marginTop: '-2px' }}>/ 100</span>
            </div>
        </div>
    )
}

function Initials({ name }) {
    const parts = name.trim().split(' ')
    const initials = parts.length >= 2
        ? parts[0][0] + parts[parts.length - 1][0]
        : name.slice(0, 2)
    return (
        <div style={{
            width: 48, height: 48, borderRadius: '50%', flexShrink: 0,
            background: 'linear-gradient(135deg, #7c3aed, #06b6d4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: "'Space Grotesk',sans-serif", fontWeight: '700', fontSize: '16px', color: '#fff',
        }}>
            {initials.toUpperCase()}
        </div>
    )
}

export default function CandidateCard({ candidate }) {
    const [expanded, setExpanded] = useState(false)
    const { profile, score, explanation, strengths, gaps, rank } = candidate
    const rankStyle = RANK_COLORS[rank] || RANK_COLORS[5]
    const sourceBadge = SOURCE_BADGES[profile.source] || SOURCE_BADGES.internal

    return (
        <div
            className="glass fade-in"
            id={`candidate-card-${rank}`}
            style={{
                ...styles.card,
                borderColor: rankStyle.border,
                animationDelay: `${(rank - 1) * 0.08}s`,
                boxShadow: rank === 1 ? '0 0 40px rgba(251,191,36,0.12)' : undefined,
            }}
        >
            {/* ── Top section ── */}
            <div style={styles.top}>

                {/* Rank badge */}
                <div style={{ ...styles.rankBadge, background: rankStyle.bg, color: rankStyle.text, borderColor: rankStyle.border }}>
                    {rankStyle.label}
                </div>

                {/* Avatar + name */}
                <div style={styles.identity}>
                    {profile.avatar_url
                        ? <img src={profile.avatar_url} alt={profile.name} style={styles.avatar} onError={e => { e.target.style.display = 'none' }} />
                        : <Initials name={profile.name} />
                    }
                    <div style={styles.nameBlock}>
                        <h3 style={styles.name}>{profile.name}</h3>
                        <p style={styles.titleLine}>
                            {profile.title}
                            {profile.current_company && <span style={styles.atCompany}> @ {profile.current_company}</span>}
                        </p>
                        <p style={styles.location}>📍 {profile.location} · {profile.years_experience}y exp</p>
                    </div>
                </div>

                {/* Score ring */}
                <ScoreRing score={score} />
            </div>

            {/* ── Source + skills ── */}
            <div style={styles.meta}>
                <span style={{ ...styles.sourceBadge, color: sourceBadge.color, background: sourceBadge.bg }}>
                    {sourceBadge.label}
                </span>
                <div style={styles.skills}>
                    {profile.skills.slice(0, 5).map(s => (
                        <span key={s} className="chip chip-default" style={{ fontSize: '10px' }}>{s}</span>
                    ))}
                    {profile.skills.length > 5 && (
                        <span style={styles.moreChip}>+{profile.skills.length - 5}</span>
                    )}
                </div>
            </div>

            {/* ── AI Explanation ── */}
            <p style={styles.explanation}>
                <span style={styles.aiLabel}>✨ AI Match:</span> {explanation}
            </p>

            {/* ── Expandable strengths/gaps ── */}
            <button
                id={`toggle-details-${rank}`}
                style={styles.expandBtn}
                onClick={() => setExpanded(e => !e)}
                aria-expanded={expanded}
            >
                {expanded ? '▲ Hide details' : '▼ View strengths & gaps'}
            </button>

            {expanded && (
                <div style={styles.details}>
                    {strengths?.length > 0 && (
                        <div style={styles.detailSection}>
                            <p style={styles.detailLabel}>✅ Strengths</p>
                            <ul style={styles.list}>
                                {strengths.map((s, i) => <li key={i} style={styles.listItem}>{s}</li>)}
                            </ul>
                        </div>
                    )}
                    {gaps?.length > 0 && (
                        <div style={styles.detailSection}>
                            <p style={styles.detailLabel}>⚠️ Gaps</p>
                            <ul style={styles.list}>
                                {gaps.map((g, i) => <li key={i} style={styles.listItem}>{g}</li>)}
                            </ul>
                        </div>
                    )}
                </div>
            )}

            {/* ── Profile links ── */}
            <div style={styles.links}>
                {profile.linkedin_url && (
                    <a href={profile.linkedin_url} target="_blank" rel="noreferrer" style={styles.link} id={`link-linkedin-${rank}`}>
                        💼 LinkedIn
                    </a>
                )}
                {profile.github_url && (
                    <a href={profile.github_url} target="_blank" rel="noreferrer" style={styles.link} id={`link-github-${rank}`}>
                        🐙 GitHub
                    </a>
                )}
                {profile.education && (
                    <span style={styles.edu}>🎓 {profile.education}</span>
                )}
            </div>
        </div>
    )
}

const styles = {
    card: {
        padding: '24px',
        transition: 'all 0.3s ease',
        cursor: 'default',
    },
    top: {
        display: 'flex',
        alignItems: 'flex-start',
        gap: '14px',
        marginBottom: '14px',
        flexWrap: 'wrap',
    },
    rankBadge: {
        fontFamily: "'Space Grotesk',sans-serif",
        fontWeight: '700',
        fontSize: '12px',
        padding: '4px 10px',
        borderRadius: '100px',
        border: '1px solid',
        flexShrink: 0,
        alignSelf: 'flex-start',
        marginTop: '2px',
    },
    identity: {
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        flex: 1,
        minWidth: '200px',
    },
    avatar: {
        width: 48,
        height: 48,
        borderRadius: '50%',
        objectFit: 'cover',
        flexShrink: 0,
        background: 'rgba(255,255,255,0.06)',
    },
    nameBlock: { flex: 1 },
    name: {
        fontFamily: "'Space Grotesk',sans-serif",
        fontWeight: '700',
        fontSize: '17px',
        color: '#f1f5f9',
        lineHeight: '1.2',
    },
    titleLine: {
        fontSize: '13px',
        color: 'rgba(255,255,255,0.55)',
        marginTop: '3px',
    },
    atCompany: { color: 'rgba(255,255,255,0.35)' },
    location: {
        fontSize: '12px',
        color: 'rgba(255,255,255,0.35)',
        marginTop: '4px',
    },
    meta: {
        display: 'flex',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '8px',
        marginBottom: '12px',
    },
    sourceBadge: {
        fontSize: '11px',
        fontWeight: '600',
        padding: '3px 10px',
        borderRadius: '100px',
        flexShrink: 0,
    },
    skills: {
        display: 'flex',
        flexWrap: 'wrap',
        gap: '5px',
    },
    moreChip: {
        fontSize: '10px',
        color: 'rgba(255,255,255,0.35)',
        padding: '3px 8px',
    },
    explanation: {
        fontSize: '13px',
        color: 'rgba(255,255,255,0.6)',
        lineHeight: '1.6',
        background: 'rgba(255,255,255,0.03)',
        borderRadius: '8px',
        padding: '10px 12px',
        marginBottom: '10px',
    },
    aiLabel: {
        color: '#a855f7',
        fontWeight: '600',
    },
    expandBtn: {
        background: 'none',
        border: 'none',
        color: 'rgba(255,255,255,0.3)',
        fontSize: '12px',
        cursor: 'pointer',
        fontFamily: 'inherit',
        padding: '4px 0',
        transition: 'color 0.2s',
    },
    details: {
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '12px',
        marginTop: '10px',
        padding: '12px',
        background: 'rgba(255,255,255,0.02)',
        borderRadius: '8px',
        animation: 'fadeIn 0.3s ease',
    },
    detailSection: {},
    detailLabel: {
        fontSize: '11px',
        fontWeight: '600',
        color: 'rgba(255,255,255,0.45)',
        textTransform: 'uppercase',
        letterSpacing: '0.07em',
        marginBottom: '6px',
    },
    list: {
        listStyle: 'none',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
    },
    listItem: {
        fontSize: '12px',
        color: 'rgba(255,255,255,0.5)',
        paddingLeft: '8px',
        position: 'relative',
    },
    links: {
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        marginTop: '12px',
        flexWrap: 'wrap',
    },
    link: {
        fontSize: '12px',
        color: 'rgba(255,255,255,0.4)',
        textDecoration: 'none',
        background: 'rgba(255,255,255,0.04)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: '6px',
        padding: '4px 10px',
        transition: 'all 0.2s ease',
    },
    edu: {
        fontSize: '11px',
        color: 'rgba(255,255,255,0.3)',
    },
}
