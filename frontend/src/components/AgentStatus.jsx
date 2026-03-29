/**
 * components/AgentStatus.jsx
 *
 * Displays a row of 3 agent status cards:
 *   🗃️ HydraDB Internal  |  💼 LinkedIn  |  🐙 GitHub
 *
 * Each card shows:
 *   - Agent name + icon
 *   - Status badge (done ✓ / error ✗)
 *   - Number of candidates found
 *   - Duration in ms
 *
 * The "running" state (shown while loading on Home page)
 * could be added later with SSE streaming. For now we show
 * the final status from the API response.
 */

const AGENT_META = {
    'HydraDB Internal': { icon: '🗃️', color: '#a855f7' },
    'GitHub': { icon: '🐙', color: '#06b6d4' },
    'LinkedIn': { icon: '💼', color: '#10b981' },
}

export default function AgentStatus({ statuses }) {
    return (
        <div style={styles.grid} role="list" aria-label="Agent search results">
            {statuses.map((s, i) => {
                const meta = AGENT_META[s.name] || { icon: '🤖', color: '#a855f7' }
                const isError = s.status === 'error'

                return (
                    <div
                        key={s.name}
                        className="glass fade-in"
                        role="listitem"
                        style={{
                            ...styles.card,
                            animationDelay: `${i * 0.1}s`,
                            borderColor: isError
                                ? 'rgba(239,68,68,0.3)'
                                : `${meta.color}30`,
                        }}
                    >
                        <div style={styles.cardTop}>
                            <span style={styles.agentIcon}>{meta.icon}</span>
                            <div style={styles.agentInfo}>
                                <p style={styles.agentName}>{s.name}</p>
                                <p style={styles.agentSource}>Search Agent</p>
                            </div>
                            <div
                                style={{
                                    ...styles.badge,
                                    background: isError
                                        ? 'rgba(239,68,68,0.15)'
                                        : 'rgba(16,185,129,0.15)',
                                    color: isError ? '#fca5a5' : '#6ee7b7',
                                    border: `1px solid ${isError ? 'rgba(239,68,68,0.3)' : 'rgba(16,185,129,0.3)'}`,
                                }}
                            >
                                {isError ? '✗ Error' : '✓ Done'}
                            </div>
                        </div>

                        <div style={styles.stats}>
                            <div style={styles.stat}>
                                <span style={{ ...styles.statNum, color: meta.color }}>
                                    {isError ? '0' : s.results_count}
                                </span>
                                <span style={styles.statLabel}>candidates found</span>
                            </div>
                            {s.duration_ms != null && (
                                <div style={styles.stat}>
                                    <span style={{ ...styles.statNum, color: 'rgba(255,255,255,0.5)' }}>
                                        {Math.round(s.duration_ms)}ms
                                    </span>
                                    <span style={styles.statLabel}>duration</span>
                                </div>
                            )}
                        </div>

                        {isError && s.error && (
                            <p style={styles.errorText} title={s.error}>
                                {s.error.slice(0, 80)}{s.error.length > 80 ? '…' : ''}
                            </p>
                        )}

                        {/* Accent bar */}
                        <div
                            style={{
                                position: 'absolute',
                                bottom: 0,
                                left: 0,
                                right: 0,
                                height: '2px',
                                background: isError
                                    ? 'rgba(239,68,68,0.4)'
                                    : `linear-gradient(90deg, ${meta.color}80, transparent)`,
                                borderRadius: '0 0 14px 14px',
                            }}
                        />
                    </div>
                )
            })}
        </div>
    )
}

const styles = {
    grid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '16px',
    },
    card: {
        position: 'relative',
        padding: '20px',
        overflow: 'hidden',
    },
    cardTop: {
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        marginBottom: '16px',
    },
    agentIcon: { fontSize: '28px' },
    agentInfo: { flex: 1 },
    agentName: {
        fontFamily: "'Space Grotesk', sans-serif",
        fontWeight: '600',
        fontSize: '15px',
        color: '#f1f5f9',
    },
    agentSource: {
        fontSize: '11px',
        color: 'rgba(255,255,255,0.35)',
        marginTop: '2px',
    },
    badge: {
        fontSize: '11px',
        fontWeight: '600',
        padding: '3px 10px',
        borderRadius: '100px',
        whiteSpace: 'nowrap',
    },
    stats: {
        display: 'flex',
        gap: '24px',
    },
    stat: {
        display: 'flex',
        flexDirection: 'column',
        gap: '2px',
    },
    statNum: {
        fontFamily: "'Space Grotesk', sans-serif",
        fontWeight: '700',
        fontSize: '22px',
    },
    statLabel: {
        fontSize: '11px',
        color: 'rgba(255,255,255,0.35)',
    },
    errorText: {
        marginTop: '10px',
        fontSize: '11px',
        color: '#fca5a5',
        background: 'rgba(239,68,68,0.08)',
        borderRadius: '6px',
        padding: '6px 10px',
    },
}
