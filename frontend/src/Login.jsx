import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
// Importamos las imágenes
import logoImg from './assets/logo.png';
import googleIcon from './assets/google.png';

// USAMOS DIRECTAMENTE LA URL DE RENDER
const API = 'https://gmail-ai-agent-l7i0.onrender.com';

function Login() {
  const navigate = useNavigate();
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
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
    window.location.href = `${API}/login`;
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <img
            src={logoImg}
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
                src={googleIcon}
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