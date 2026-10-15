import { Bricolage_Grotesque, IBM_Plex_Sans, IBM_Plex_Sans_Arabic, JetBrains_Mono } from 'next/font/google'

export const display = Bricolage_Grotesque({ subsets: ['latin'], variable: '--font-display', display: 'swap' })
export const body = IBM_Plex_Sans({ subsets: ['latin'], weight: ['400', '500', '600', '700'], style: ['normal', 'italic'], variable: '--font-latin', display: 'swap' })
export const arabic = IBM_Plex_Sans_Arabic({ subsets: ['arabic'], weight: ['400', '500', '600', '700'], variable: '--font-arabic', display: 'swap' })
export const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono', display: 'swap' })
export const fontVars = [display.variable, body.variable, arabic.variable, mono.variable].join(' ')

/** Set theme before first paint (no flash). */
export const themeScript = `try{var t=localStorage.getItem('atl_theme');document.documentElement.dataset.theme=t||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')}catch(e){document.documentElement.dataset.theme='light'}`
