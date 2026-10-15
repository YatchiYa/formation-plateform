'use client'
import { useEffect, useRef, useState } from 'react'

const FRAME_W = 1280

/** Renders the real page in an iframe and paints click density on a canvas on top of it. */
export function HeatmapView({ path, points }: { path: string; points: { x: number; y: number; vw: number; dh: number }[] }) {
  const frame = useRef<HTMLIFrameElement>(null)
  const canvas = useRef<HTMLCanvasElement>(null)
  const wrap = useRef<HTMLDivElement>(null)
  const [height, setHeight] = useState(Math.max(900, ...points.map((p) => p.y + 40)))
  const [scale, setScale] = useState(1)

  useEffect(() => {
    const fit = () => setScale(Math.min(1, (wrap.current?.clientWidth ?? FRAME_W) / FRAME_W))
    fit()
    addEventListener('resize', fit)
    return () => removeEventListener('resize', fit)
  }, [])

  useEffect(() => {
    const c = canvas.current!
    c.width = FRAME_W
    c.height = height
    const ctx = c.getContext('2d')!
    ctx.clearRect(0, 0, c.width, c.height)
    // Accumulate soft blobs, then map alpha to a cool->hot color ramp.
    for (const p of points) {
      const x = (p.x / 100) * FRAME_W
      const g = ctx.createRadialGradient(x, p.y, 0, x, p.y, 28)
      g.addColorStop(0, 'rgba(0,0,0,0.35)')
      g.addColorStop(1, 'rgba(0,0,0,0)')
      ctx.fillStyle = g
      ctx.fillRect(x - 28, p.y - 28, 56, 56)
    }
    const img = ctx.getImageData(0, 0, c.width, c.height)
    const d = img.data
    for (let i = 0; i < d.length; i += 4) {
      const a = d[i + 3] / 255
      if (!a) continue
      const t = Math.min(1, a * 1.6)
      d[i] = Math.round(40 + 215 * t)
      d[i + 1] = Math.round(120 + 100 * (1 - Math.abs(t - 0.5) * 2) - 60 * t)
      d[i + 2] = Math.round(255 * (1 - t))
      d[i + 3] = Math.round(Math.min(0.85, 0.25 + t) * 255)
    }
    ctx.putImageData(img, 0, 0)
  }, [points, height])

  const onLoad = () => {
    try {
      const h = frame.current?.contentDocument?.documentElement.scrollHeight
      if (h) setHeight(Math.max(h, ...points.map((p) => p.y + 40)))
    } catch {}
  }

  return (
    <div className="heat-wrap" ref={wrap} style={{ height: height * scale }}>
      <div className="heat-stage" style={{ width: FRAME_W, height, transform: `scale(${scale})` }}>
        <iframe ref={frame} src={path} title="Aperçu de la page" onLoad={onLoad} style={{ width: FRAME_W, height }} scrolling="no" />
        <canvas ref={canvas} className="heat-canvas" aria-label={`${points.length} clics`} />
      </div>
      <p className="heat-count">{points.length} clics affichés</p>
    </div>
  )
}
