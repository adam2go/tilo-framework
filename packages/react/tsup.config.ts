import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm", "cjs"],
  dts: true,
  splitting: false,
  sourcemap: true,
  clean: true,
  // All React-ecosystem packages stay external to avoid bundle conflicts.
  external: ["react", "react-dom", "recharts", "lucide-react"],
  // "use client" must appear at the top of the compiled output so Next.js
  // App Router and other RSC-aware bundlers correctly scope these modules.
  banner: {
    js: '"use client";',
  },
  esbuildOptions(options) {
    options.jsx = "automatic";
  },
});
