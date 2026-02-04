# Gmail AI Agent

Agente inteligente para gestión de correos de Gmail. Utiliza **FastAPI** (Python) en el backend y **React** (Vite) en el frontend. Integra IA (Gemini) para resumir correos, detectar reuniones y gestionar el calendario automáticamente.

## 🚀 Requisitos Previos

* Python 3.8+
* Node.js & npm
* Cuenta de Google Cloud (con Gmail API y Calendar API habilitadas)

---

## ⚙️ Configuración de Secretos (IMPORTANTE)

Como este proyecto usa OAuth y APIs, necesitas añadir tus claves manualmente (no se suben a GitHub por seguridad).

1.  **Backend:** Crea un archivo `.env` en la raíz con tu API KEY de Gemini:
    ```
    GOOGLE_API_KEY=tu_api_key_aqui
    ```
2.  **OAuth:** Coloca tu archivo de credenciales de Google en:
    ```
    app/auth/client_secret.json
    ```

---

## 🛠️ Instalación y Arranque

Necesitarás **dos terminales** abiertas: una para el Backend y otra para el Frontend.

### 1. Backend (Terminal 1)

Desde la carpeta raíz del proyecto:

```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno (Windows)
venv\Scripts\activate
# (Deberías ver (venv) al inicio de la línea de comandos)

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Arrancar servidor
uvicorn app.main:app --reload --port 8001
