import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

function ProtectedRoute({ children }) {
  const [loading, setLoading] = useState(true);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8001/auth/status", {
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
