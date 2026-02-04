import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

function Login() {
  const navigate = useNavigate();
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8001/auth/status", {
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
    window.location.href = "http://localhost:8001/login";
  }

  return (
    <div className="login-container">
      <div className="login-card">
        {/* Logo principal */}
        <div className="login-header">
          <img
            src="/src/assets/logo.png"
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
                src="/src/assets/google.png"
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