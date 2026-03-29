/**
 * components/PromptInput.jsx
 *
 * The main search input card on the Home page.
 *
 * Features:
 *  - Multi-line textarea with character counter
 *  - One-click "example chips" that fill the textarea
 *  - Submit button with spinner while loading
 *  - Keyboard shortcut: Cmd/Ctrl+Enter to submit
 */
import { useState, useRef, useCallback } from 'react'

export default function PromptInput({ onSearch, loading, examples }) {
    const [value, setValue] = useState('')
    const ref = useRef(null)

    const handleKeyDown = useCallback(
        (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && value.trim().length >= 10) {
                onSearch(value.trim())
            }
        },
        [value, onSearch],
    )

    const fillExample = (ex) => {
        setValue(ex)
        ref.current?.focus()
    }

    const canSubmit = value.trim().length >= 10 && !loading

    return (
        <div className="glass" style={styles.card}>
            <label htmlFor="prompt-input" style={styles.label}>
                Describe your ideal candidate
            </label>

            <textarea
                id="prompt-input"
                ref={ref}
                value={value}
                onChange={e => setValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="e.g. Software engineer focused on distributed systems, 3+ years experience, AI/ML background, preferably in San Francisco..."
                style={styles.textarea}
                rows={4}
                disabled={loading}
                aria-label="Candidate requirements"
            />

            <div style={styles.footer}>
                {/* Example chips */}
                <div style={styles.chips}>
                    <span style={styles.chipsLabel}>Quick fill:</span>
                    {examples.slice(0, 3).map((ex, i) => (
                        <button
                            key={i}
                            id={`example-chip-${i}`}
                            className="chip chip-default"
                            onClick={() => fillExample(ex)}
                            disabled={loading}
                            style={{ cursor: 'pointer', border: 'none', fontFamily: 'inherit' }}
                            title={ex}
                        >
                            {ex.split(',')[0].slice(0, 24)}…
                        </button>
                    ))}
                </div>

                <div style={styles.rightSection}>
                    <span style={styles.charCount}>{value.length} chars</span>
                    <button
                        id="btn-search"
                        className="btn btn-primary"
                        onClick={() => onSearch(value.trim())}
                        disabled={!canSubmit}
                        style={{ minWidth: '160px' }}
                    >
                        {loading ? (
                            <>
                                <div className="spinner" />
                                Searching…
                            </>
                        ) : (
                            <>🔍 Find Candidates</>
                        )}
                    </button>
                </div>
            </div>

            <p style={styles.hint}>
                Press <kbd style={styles.kbd}>⌘ Enter</kbd> to search · Be as specific as you like
            </p>
        </div>
    )
}

const styles = {
    card: {
        padding: '28px 32px',
        maxWidth: '760px',
        margin: '0 auto',
    },
    label: {
        display: 'block',
        fontFamily: "'Space Grotesk', sans-serif",
        fontWeight: '600',
        fontSize: '15px',
        color: 'rgba(255,255,255,0.75)',
        marginBottom: '12px',
    },
    textarea: {
        width: '100%',
        background: 'rgba(255,255,255,0.06)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '10px',
        color: '#f1f5f9',
        fontSize: '15px',
        lineHeight: '1.6',
        padding: '14px 16px',
        resize: 'vertical',
        outline: 'none',
        fontFamily: "'Inter', sans-serif",
        transition: 'border-color 0.2s ease',
        minHeight: '110px',
    },
    footer: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
        marginTop: '14px',
    },
    chips: {
        display: 'flex',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '6px',
    },
    chipsLabel: {
        fontSize: '12px',
        color: 'rgba(255,255,255,0.3)',
        marginRight: '4px',
    },
    rightSection: {
        display: 'flex',
        alignItems: 'center',
        gap: '14px',
    },
    charCount: {
        fontSize: '12px',
        color: 'rgba(255,255,255,0.25)',
    },
    hint: {
        marginTop: '10px',
        fontSize: '12px',
        color: 'rgba(255,255,255,0.25)',
    },
    kbd: {
        background: 'rgba(255,255,255,0.08)',
        border: '1px solid rgba(255,255,255,0.12)',
        borderRadius: '4px',
        padding: '1px 6px',
        fontSize: '11px',
        fontFamily: 'monospace',
    },
}
