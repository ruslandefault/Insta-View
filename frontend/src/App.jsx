import { useEffect, useState } from "react";

export default function App() {
  const [status, setStatus] = useState("tekshirilmoqda...");

  useEffect(() => {
    // Vite proxy orqali FastAPI backendga so'rov
    fetch("/api/health")
      .then((res) => res.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus("backend bilan aloqa yo'q"));
  }, []);

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>Insta View</h1>
      <p>Backend holati: <strong>{status}</strong></p>
    </main>
  );
}
