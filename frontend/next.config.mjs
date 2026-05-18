const backendUrl = process.env.BACKEND_URL;

/** @type {import('next').NextConfig} */
const nextConfig = {
	env: {
		NEXT_PUBLIC_BACKEND_URL: backendUrl,
	},
};

export default nextConfig;
