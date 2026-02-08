/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'wkzlezxxtbqfodyustav.supabase.co',
      },
    ],
  },
}

module.exports = nextConfig
