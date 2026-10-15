import fs from 'node:fs'
import path from 'node:path'
import { DatabaseSync } from 'node:sqlite'

const DATA_DIR = path.resolve(process.env.DATA_DIR || path.join(/* turbopackIgnore: true */ process.cwd(), 'data'))

const g = globalThis as unknown as { __db?: DatabaseSync }

// ponytail: single SQLite file, fine for one container and ~millions of events; move to Postgres if you scale out to several replicas.
export function db(): DatabaseSync {
  if (g.__db) return g.__db
  fs.mkdirSync(DATA_DIR, { recursive: true })
  const d = new DatabaseSync(path.join(DATA_DIR, 'analytics.db'))
  d.exec(`
    PRAGMA journal_mode = WAL;
    PRAGMA busy_timeout = 3000;
    CREATE TABLE IF NOT EXISTS events (
      id INTEGER PRIMARY KEY,
      ts INTEGER NOT NULL,
      type TEXT NOT NULL,          -- pageview | click | leave | download
      visitor TEXT NOT NULL,
      session TEXT,
      path TEXT NOT NULL,
      locale TEXT,
      referrer TEXT,
      device TEXT,
      browser TEXT,
      country TEXT,
      x REAL, y REAL, vw INTEGER, dh INTEGER,   -- click position: x in % of width, y in px from top
      target TEXT, href TEXT,
      value INTEGER                -- leave: seconds on page; scroll depth in "scroll"
    );
    CREATE INDEX IF NOT EXISTS ev_ts ON events(ts);
    CREATE INDEX IF NOT EXISTS ev_type_path ON events(type, path);
    -- Visitors are anonymous today; user_id links them to an account once sign-in exists.
    CREATE TABLE IF NOT EXISTS visitors (id TEXT PRIMARY KEY, user_id TEXT, first_seen INTEGER, last_seen INTEGER);
    CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email TEXT UNIQUE, name TEXT, plan TEXT DEFAULT 'free', created INTEGER);
    CREATE TABLE IF NOT EXISTS progress (
      visitor TEXT NOT NULL,
      item TEXT NOT NULL,          -- content url, e.g. /ia-generative/rag-gcp/fondamentaux/introduction
      course TEXT,
      status TEXT NOT NULL DEFAULT 'started',  -- started | completed
      pct INTEGER DEFAULT 0,
      updated INTEGER NOT NULL,
      PRIMARY KEY (visitor, item)
    );
  `)
  g.__db = d
  return d
}

export function deviceOf(ua: string) {
  const device = /ipad|tablet/i.test(ua) ? 'tablet' : /mobi|android|iphone/i.test(ua) ? 'mobile' : 'desktop'
  const browser = /edg\//i.test(ua) ? 'Edge' : /firefox/i.test(ua) ? 'Firefox' : /chrome|crios/i.test(ua) ? 'Chrome' : /safari/i.test(ua) ? 'Safari' : 'Other'
  return { device, browser }
}

export const isBot = (ua: string) => process.env.TRACK_BOTS !== '1' && /bot|crawl|spider|slurp|headless|lighthouse/i.test(ua)
