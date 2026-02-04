import os
import json
import re
from datetime import datetime

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

# =========================
# GEMINI CONFIG
# =========================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY no encontrada en variables de entorno")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash-lite")
##gemini-2.5-flash-lite
#gemini-3-flash-preview

# =========================
# MAIN FUNCTION
# =========================
def analyze_email_structured(email_text: str):
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    weekday_str = today.strftime("%A")

    
    prompt = f"""
Eres un sistema automático de análisis de correos electrónicos.

HOY ES:
- Fecha actual: {today_str}
- Día de la semana: {weekday_str}

Debes interpretar fechas como lo haría una persona.

REGLAS DE INTERPRETACIÓN DE FECHAS:
- Si se menciona solo un día del mes (ej. "el 25"):
  usa el MES ACTUAL si la fecha aún no ha pasado,
  o el MES SIGUIENTE si ya pasó.
- Si se menciona un día de la semana (ej. "domingo 25"):
  calcula la fecha correcta a partir de la fecha actual.
- Si no se menciona el año, usa el año correspondiente según el cálculo.
- Si se menciona una hora, inclúyela.
- Si no se menciona duración, usa 60 minutos.

Instrucciones:
1. Analiza el correo recibido.
2. Extrae la intención y datos clave.
3. GENERA SIEMPRE UNA RESPUESTA SUGERIDA (suggested_reply).
   - Si el correo es una conversación: Redacta una respuesta natural y profesional.
   - Si es una newsletter o notificación: Redacta un simple "Recibido, gracias" o "Leído".
   - NO dejes el campo suggested_reply vacío o null.

REGLAS DE SALIDA (CRÍTICO):
- RESPONDE ÚNICAMENTE CON JSON
- EL PRIMER CARÁCTER DE LA RESPUESTA DEBE SER {{
- EL ÚLTIMO CARÁCTER DE LA RESPUESTA DEBE SER }}
- NO escribas texto antes ni después
- NO uses markdown
- NO uses ``` 
- NO expliques nada
- NO añadas comentarios
- NO añadas notas
- NO incluyas explicaciones
- NO incluyas texto adicional
- NO escribas nada fuera del JSON

El JSON debe tener EXACTAMENTE esta estructura:

{{
  "summary": string,
  "meeting_detected": boolean,
  "proposed_datetime": "YYYY-MM-DDTHH:MM" o null,
  "duration_minutes": number o null,
  "suggested_reply": string,
  "suggested_label": string o null
}}

REGLAS PARA suggested_label:
- Usa UNA sola etiqueta corta y humana
- Ejemplos: Trabajo, Facturas, Soporte, Newsletter, Personal
- Si no hay categoría clara, usa null

Correo:
<EMAIL>
{email_text}
</EMAIL>
"""

    # =========================
    # GEMINI CALL
    # =========================
    try:
       
        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(
                response_mime_type="application/json"
            )
        )
        text = response.text or ""
    except Exception as e:
        print(f"❌ ERROR GEMINI: {e}")
        return {
            "summary": "Error analizando correo",
            "meeting_detected": False,
            "proposed_datetime": None,
            "duration_minutes": None,
            "suggested_reply": "",
            "suggested_label": None,
            "error": str(e),
        }

    # =========================
    # PARSE JSON 
    # =========================
    try:
     
        data = json.loads(text)
    except Exception:
        
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return {
                "summary": "Correo analizado (modo demo)",
                "meeting_detected": False,
                "proposed_datetime": None,
                "duration_minutes": None,
                "suggested_reply": "Gracias por tu correo. Lo reviso y te confirmo en breve.",
                "suggested_label": "trabajo",
                "raw_output": text,
            }
        try:
            data = json.loads(match.group(0))
        except:
             return {
                "summary": "Error procesando JSON",
                "meeting_detected": False,
                "error": "Invalid JSON format"
            }

    # =========================
    # NORMALIZE LABEL
    # =========================
    if data.get("suggested_label"):
        label = data["suggested_label"].strip().lower()

        LABEL_MAP = {
            "factura": "facturas",
            "facturas": "facturas",
            "pagos": "facturas",
            "recibos": "facturas",
            "cobros": "facturas", 
            "newsletter": "newsletter",
            "newsletters": "newsletter",
            "promociones": "newsletter",
            "trabajo": "trabajo",
            "proyectos": "trabajo",
            "reuniones": "trabajo",
            "personal": "personal",
            "soporte": "soporte",
            "incidencias": "soporte",
        }

        # Búsqueda parcial si no hay match exacto
        # (Mantiene tu lógica pero la hace más resistente si la IA dice "Reunión de trabajo")
        found = LABEL_MAP.get(label)
        if not found:
             for key, val in LABEL_MAP.items():
                 if key in label:
                     found = val
                     break
        
        data["suggested_label"] = found

    return data