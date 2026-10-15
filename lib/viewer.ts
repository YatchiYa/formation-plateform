import { cookies } from 'next/headers'
import type { Meta } from './content'
import { VISITOR_COOKIE } from './constants'

export interface Viewer { visitorId: string | null; user: null | { id: string; plan: 'free' | 'premium' } }

/** Today every viewer is anonymous. Plug the session lookup (Auth.js, Lucia...) here when accounts land. */
export async function getViewer(): Promise<Viewer> {
  const jar = await cookies()
  return { visitorId: jar.get(VISITOR_COOKIE)?.value ?? null, user: null }
}

/**
 * Single access gate for every page. Premium content is readable by everyone until
 * PREMIUM_GATE=on, then it requires a premium user (others see a teaser).
 */
export function canRead(meta: Pick<Meta, 'access'>, viewer: Viewer) {
  if (meta.access !== 'premium' || process.env.PREMIUM_GATE !== 'on') return true
  return viewer.user?.plan === 'premium'
}
