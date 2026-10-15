import { NextResponse, type NextRequest } from 'next/server'
import { defaultLocale, isLocale } from './lib/i18n'
import { VISITOR_COOKIE } from './lib/constants'

function preferredLocale(req: NextRequest) {
  const c = req.cookies.get('atl_locale')?.value
  if (c && isLocale(c)) return c
  for (const part of (req.headers.get('accept-language') || '').split(',')) {
    const code = part.trim().slice(0, 2).toLowerCase()
    if (isLocale(code)) return code
  }
  return defaultLocale
}

function adminAuthorized(req: NextRequest) {
  const pass = process.env.ADMIN_PASSWORD
  if (!pass) return false
  const [scheme, token] = (req.headers.get('authorization') || '').split(' ')
  if (scheme !== 'Basic' || !token) return false
  const [u, ...p] = atob(token).split(':')
  return u === (process.env.ADMIN_USER || 'admin') && p.join(':') === pass
}

export function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl
  const first = pathname.split('/')[1]

  if (first === 'admin' || pathname.startsWith('/api/admin')) {
    if (!process.env.ADMIN_PASSWORD) return new NextResponse('Admin disabled: set ADMIN_PASSWORD.', { status: 404 })
    if (!adminAuthorized(req)) return new NextResponse('Authentication required', { status: 401, headers: { 'WWW-Authenticate': 'Basic realm="admin"' } })
    return NextResponse.next()
  }

  let res: NextResponse
  if (first === 'api' || first === 'files') res = NextResponse.next()
  else if (!isLocale(first)) {
    const url = req.nextUrl.clone()
    url.pathname = `/${preferredLocale(req)}${pathname === '/' ? '' : pathname}`
    res = NextResponse.redirect(url)
  } else res = NextResponse.next()

  if (!req.cookies.get(VISITOR_COOKIE)) {
    res.cookies.set(VISITOR_COOKIE, crypto.randomUUID(), { maxAge: 60 * 60 * 24 * 365, sameSite: 'lax', httpOnly: true, path: '/' })
  }
  return res
}

export const config = {
  matcher: ['/((?!_next/|favicon\\.ico|icon\\.svg|robots\\.txt|sitemap\\.xml).*)'],
}

