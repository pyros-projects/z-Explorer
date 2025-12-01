import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte({ hot: !process.env.VITEST })],
  test: {
    include: ['src/**/*.{test,spec}.{js,ts}'],
    passWithNoTests: true,
    environment: 'jsdom',
    globals: true,
    setupFiles: ['src/__tests__/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      // Only track coverage for new code (services, stores)
      // Exclude existing components until they're refactored
      include: ['src/lib/services/**/*.ts', 'src/lib/stores/**/*.ts'],
      exclude: ['src/**/*.test.ts', 'src/**/*.spec.ts', 'src/__tests__/**'],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
    // Reduce noise in test output
    reporters: ['default'],
    // Make sure Svelte components are properly handled
    alias: {
      '$lib': '/src/lib',
    },
  },
});
