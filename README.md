# Gmail AI Agent

Agente inteligente para la gestión de correos de Gmail. Utiliza **FastAPI** (Python) en el backend y **React** (Vite) en el frontend. Integra IA (Google Gemini) para resumir correos, detectar reuniones, gestionar el calendario y sugerir respuestas.

## 🚀 Requisitos Previos

* Python 3.8+
* Node.js & npm
* Cuenta de Google Cloud (con Gmail API y Calendar API habilitadas)

---

## ⚙️ Configuración de Secretos (IMPORTANTE)

⚠️ **Nota:** Los archivos de configuración de claves no se incluyen en el repositorio por seguridad. **Debes crearlos manualmente** si clonas este proyecto en un nuevo equipo:

1.  **Backend (.env):** Crea un archivo llamado `.env` en la carpeta raíz del proyecto con tu clave de Gemini:
    ```env
    GOOGLE_API_KEY=tu_api_key_aqui
    ```

2.  **OAuth (client_secret.json):** Coloca el archivo JSON de credenciales descargado de Google Cloud en la siguiente ruta:
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
# (Verás (venv) al inicio de la línea de comandos)

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Arrancar servidor backend
uvicorn app.main:app --reload --port 8001
```
Déjalo abierto. El backend estará escuchando en http://localhost:8001.

2. Frontend (Terminal 2)
Desde la carpeta raíz del proyecto:
```bash
# 1. Entrar a la carpeta frontend
cd frontend

# 2. Instalar dependencias (solo la primera vez)
npm install

# 3. Arrancar servidor de desarrollo
npm run dev
```
Debe decir algo como: Local: http://localhost:5173

🌐 Uso
Abre tu navegador en: http://localhost:5173

Te pedirá Login. Haz clic para iniciar sesión con Google.

Acepta los permisos necesarios (Gmail y Calendar).

¡Listo! La app cargará tus correos y podrás usar las funciones de IA.

📦 Estructura del Proyecto
/app: Código fuente del Backend (FastAPI, rutas, servicios de IA).

/frontend: Código fuente del Frontend (React, Vite, CSS).

requirements.txt: Lista de dependencias de Python.
