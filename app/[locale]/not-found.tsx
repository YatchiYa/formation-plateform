import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="page empty-state">
      <p className="big-code">404</p>
      <h1 className="display display-sm">Page introuvable · Page not found</h1>
      <Link className="btn btn-primary" href="/">Accueil · Home</Link>
    </div>
  )
}
