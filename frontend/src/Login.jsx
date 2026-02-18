import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
// IMPORTANTE: Importamos las imágenes para que Vite las procese bien en producción
import logoImg from './assets/logo.png';
import googleIcon from './assets/google.png';

// Detectamos si estamos en Vercel o en Local
const API = import.meta.env.VITE_API_URL || 'http://localhost:8001';

function Login() {
  const navigate = useNavigate();
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    // Usamos la variable API en lugar de localhost
    fetch(`${API}/auth/status`, {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.logged_in) {
          navigate("/");
        }
      })
      .catch(() => {});
  }, [navigate]);

  function loginWithGoogle() {
    setConnecting(true);
    // Redirigimos al backend correcto (Render en prod, Localhost en dev)
    window.location.href = `${API}/login`;
  }

  return (
    <div className="login-container">
      <div className="login-card">
        {/* Logo principal */}
        <div className="login-header">
          <img
            src={logoImg} // Usamos la variable importada
            alt="Gmail AI Agent logo"
            className="login-logo"
          />
          <h1>Gmail AI Agent</h1>
        </div>

        <p className="login-description">
          Conecta tu cuenta de Gmail y gestiona tus correos con ayuda de IA.
        </p>

        <button
          className="google-button"
          onClick={loginWithGoogle}
          disabled={connecting}
        >
          {!connecting ? (
            <>
              <img
                src={googleIcon} // Usamos la variable importada
                alt="Google logo"
                className="google-icon"
              />
              <span>Continuar con Google</span>
            </>
          ) : (
            <span>Conectando…</span>
          )}
        </button>
        
        {connecting && (
          <p className="login-connecting-text">
            Redirigiendo a Google…
          </p>
        )}
      </div>
    </div>
  );
}

export default Login;