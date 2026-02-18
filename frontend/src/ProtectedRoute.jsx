import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

// USAMOS DIRECTAMENTE LA URL DE RENDER
const API = 'https://gmail-ai-agent-l7i0.onrender.com';

function ProtectedRoute({ children }) {
  const [loading, setLoading] = useState(true);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    fetch(`${API}/auth/status`, {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => {
        setLoggedIn(data.logged_in);
        setLoading(false);
      })
      .catch(() => {
        setLoggedIn(false);
        setLoading(false);
      });
  }, []);

  if (loading) {
    // AQUI ESTÁ EL CAMBIO: Una pantalla de carga bonita
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Conectando con tu asistente...</p>
      </div>
    );
  }

  if (!loggedIn) return <Navigate to="/login" replace />;

  return children;
}

export default ProtectedRoute;