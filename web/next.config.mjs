// Share the repo-root .env (names in .env.example) with the web app in local dev.
try {
  process.loadEnvFile("../.env");
} catch {
  /* no root .env (e.g. CI or cloud): rely on real environment variables */
}

const API = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Browser calls go to same-origin /backend/* so there is no CORS and no API URL baked into the client bundle.
  async rewrites() {
    return [{ source: "/backend/:path*", destination: `${API}/:path*` }];
  },
};

export default nextConfig;
