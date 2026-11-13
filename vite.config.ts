import { defineConfig } from 'vite';

export default defineConfig({
  // relative URLs: works at a GitHub Pages project path (/ClawdStudy/) or any other subfolder
  base: './',
  build: {
    target: 'es2022',
    chunkSizeWarningLimit: 700,
  },
});
