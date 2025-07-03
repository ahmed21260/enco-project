import React from "react";
import { createRoot } from "react-dom/client";

function App() {
  return (
    <div style={{padding: 40, textAlign: "center"}}>
      <h1>Bienvenue sur le Dashboard ENCO 🚀</h1>
      <p>Tout fonctionne !</p>
    </div>
  );
}

const root = createRoot(document.getElementById("root"));
root.render(<App />); 