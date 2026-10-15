import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'standalone',
  // Content is read from disk at request time; these must stay as real node modules.
  serverExternalPackages: ['shiki', '@shikijs/rehype', 'mammoth'],
  outputFileTracingExcludes: { '*': ['content/**', 'data/**', 'e2e/**'] },
}

export default nextConfig
