import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    ignores: [
      "dist",
      "node_modules",
      "backend/.venv",
      "backend/.pytest_cache",
      "backend/.ruff_cache",
    ],
  },
  {
    files: ["src/**/*.{ts,tsx}", "vite.config.ts", "eslint.config.js"],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
);
