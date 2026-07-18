import React from 'react'

/**
 * UniverseBadge — Presentation-only component.
 * 
 * Renders small professional badges for market universe membership.
 * Does NOT modify, access, or influence any recommendation, strategy,
 * calculation, or database system.
 * 
 * Usage:
 *   <UniverseBadge universes={['NIFTY 500', 'F&O']} />
 *   <UniverseBadge universes={session.universes} />
 * 
 * Future-proof: supports any number of universe badges.
 * If universes is empty or undefined, renders nothing.
 */

const BADGE_COLORS = {
  'NIFTY 500': {
    bg: 'rgba(99, 155, 255, 0.12)',
    border: 'rgba(99, 155, 255, 0.25)',
    text: '#639bff',
  },
  'NIFTY 200': {
    bg: 'rgba(167, 139, 250, 0.12)',
    border: 'rgba(167, 139, 250, 0.25)',
    text: '#a78bfa',
  },
  'NIFTY 100': {
    bg: 'rgba(52, 211, 153, 0.12)',
    border: 'rgba(52, 211, 153, 0.25)',
    text: '#34d399',
  },
  'F&O': {
    bg: 'rgba(251, 191, 36, 0.10)',
    border: 'rgba(251, 191, 36, 0.25)',
    text: '#fbbf24',
  },
}

const DEFAULT_BADGE_STYLE = {
  bg: 'rgba(255, 255, 255, 0.06)',
  border: 'rgba(255, 255, 255, 0.12)',
  text: 'rgba(255, 255, 255, 0.6)',
}

export default function UniverseBadge({ universes, size = 'small' }) {
  if (!universes || universes.length === 0) return null

  const fontSize = size === 'tiny' ? '0.56rem' : size === 'small' ? '0.62rem' : '0.72rem'
  const padding = size === 'tiny' ? '1px 5px' : size === 'small' ? '2px 7px' : '3px 10px'
  const gap = size === 'tiny' ? '3px' : '4px'

  return (
    <span style={{ display: 'inline-flex', gap, flexWrap: 'wrap', alignItems: 'center' }}>
      {universes.map((name) => {
        const colors = BADGE_COLORS[name] || DEFAULT_BADGE_STYLE
        return (
          <span
            key={name}
            style={{
              display: 'inline-block',
              fontSize,
              fontWeight: 700,
              letterSpacing: '0.03em',
              padding,
              borderRadius: '3px',
              background: colors.bg,
              border: `1px solid ${colors.border}`,
              color: colors.text,
              whiteSpace: 'nowrap',
              lineHeight: 1.4,
              userSelect: 'none',
            }}
          >
            {name}
          </span>
        )
      })}
    </span>
  )
}
