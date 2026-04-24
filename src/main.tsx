import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import App from "./App"
import "../app/globals.css"
// globals.css incluído via Tailwind CSS

createRoot(document.getElementById('root')!).render(
  <StrictMode> 
    <App />
  </StrictMode>, 
)
