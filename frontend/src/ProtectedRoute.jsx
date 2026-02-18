import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

// USAMOS DIRECTAMENTE LA URL DE RENDER
const API = 'https://gmail-ai-agent-l7i0.onrender.com';

function ProtectedRoute({ children }) {
  const [loading, setLoading] = useState(true);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    // AQUI ESTABA EL ERROR: cambiamos localhost por la variable API
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

  if (loading) return <p>Cargando...</p>;

  if (!loggedIn) return <Navigate to="/login" replace />;

  return children;
}

export default ProtectedRoute;