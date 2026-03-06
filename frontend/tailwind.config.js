/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#475569",
        secondary: "#64748B",
        cta: "#2563EB",
        background: {
          main: "#F8FAFC"
        },
        text: {
          main: "#1E293B"
        }
      },
      fontFamily: {
        body: ['Fira Sans', 'sans-serif'],
        heading: ['Fira Code', 'monospace'],
      },
      spacing: {
        xs: "0.25rem",
        sm: "0.5rem",
        md: "1rem",
        lg: "1.5rem",
        xl: "2rem",
        "2xl": "3rem",
        "3xl": "4rem",
      },
      boxShadow: {
        sm: "0 1px 2px rgba(0,0,0,0.05)",
        md: "0 4px 6px rgba(0,0,0,0.1)",
        lg: "0 10px 15px rgba(0,0,0,0.1)",
        xl: "0 20px 25px rgba(0,0,0,0.15)",
      }
    },
  },
  plugins: [],
}
