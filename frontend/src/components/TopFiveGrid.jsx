/**
 * components/TopFiveGrid.jsx
 *
 * Renders the ranked list of top-5 candidates.
 *
 * Layout:
 *   - #1 candidate gets a full-width featured card at the top
 *   - #2–#5 in a 2-column grid below
 *
 * Also shows a summary comparison row at the bottom
 * (average score, top location, top source).
 */
import CandidateCard from './CandidateCard'

export default function TopFiveGrid({ candidates }) {
    if (!candidates || candidates.length === 0) {
        return (
            <div style={styles.empty}>
                <p>No candidates found. Try broadening your search.</p>
            </div>
        )
    }

    const [first, ...rest] = candidates

    const avgScore = Math.round(
        candidates.reduce((sum, c) => sum + c.score, 0) / candidates.length,
    )

    return (
        <div>
            {/* #1 — featured full-width */}
            <div style={styles.featuredWrap}>
                <div style={styles.featuredLabel}>
                    <span>⭐ Best Match</span>
                </div>
                <CandidateCard candidate={first} />
            </div>

            {/* #2–#5 — 2-column grid */}
            {rest.length > 0 && (
                <div style={styles.grid}>
                    {rest.map(c => (
                        <CandidateCard key={c.profile.id} candidate={c} />
                    ))}
                </div>
            )}

            {/* ── Summary footer ── */}
            <div className="glass" style={styles.summary}>
                <div style={styles.summaryItem}>
                    <span style={styles.summaryValue}>{candidates.length}</span>
                    <span style={styles.summaryLabel}>candidates shown</span>
                </div>
                <div style={styles.sumDivider} />
                <div style={styles.summaryItem}>
                    <span style={styles.summaryValue}>{avgScore}</span>
                    <span style={styles.summaryLabel}>average match score</span>
                </div>
                <div style={styles.sumDivider} />
                <div style={styles.summaryItem}>
                    <span style={styles.summaryValue}>{first.score}</span>
                    <span style={styles.summaryLabel}>top match score</span>
                </div>
                <div style={styles.sumDivider} />
                <div style={styles.summaryItem}>
                    <span style={styles.summaryValue}>
                        {[...new Set(candidates.map(c => c.profile.source))].join(' + ')}
                    </span>
                    <span style={styles.summaryLabel}>sources searched</span>
                </div>
            </div>
        </div>
    )
}

const styles = {
    featuredWrap: {
        position: 'relative',
        marginBottom: '20px',
    },
    featuredLabel: {
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        background: 'rgba(251,191,36,0.15)',
        border: '1px solid rgba(251,191,36,0.3)',
        color: '#fbbf24',
        fontSize: '12px',
        fontWeight: '600',
        padding: '4px 12px',
        borderRadius: '100px 100px 0 0',
        marginBottom: '-1px',
        fontFamily: "'Space Grotesk',sans-serif",
    },
    grid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '16px',
        marginBottom: '24px',
    },
    summary: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-around',
        padding: '18px 24px',
        marginTop: '8px',
    },
    summaryItem: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '4px',
    },
    summaryValue: {
        fontFamily: "'Space Grotesk',sans-serif",
        fontWeight: '700',
        fontSize: '18px',
        background: 'linear-gradient(135deg, #a855f7, #06b6d4)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
        textTransform: 'capitalize',
    },
    summaryLabel: {
        fontSize: '11px',
        color: 'rgba(255,255,255,0.35)',
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
    },
    sumDivider: {
        width: '1px',
        height: '36px',
        background: 'rgba(255,255,255,0.08)',
    },
    empty: {
        textAlign: 'center',
        padding: '60px',
        color: 'rgba(255,255,255,0.3)',
        fontSize: '15px',
    },
}
