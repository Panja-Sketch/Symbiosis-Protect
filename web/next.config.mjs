// Share the repo-root .env (names in .env.example) with the web app in local dev.
try {
  process.loadEnvFile("../.env");
} catch {
  /* no root .env (CI or cloud): rely on real environment variables */
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone output is for the Docker image (Linux); Windows needs symlink privileges to produce it.
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,
  poweredByHeader: false,
};

export default nextConfig;
