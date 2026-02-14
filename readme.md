# Calendario Automático CV Bunyola 🏐

Este proyecto genera un calendario `.ics` que se actualiza automáticamente con los partidos del CV Bunyola. Puedes suscribirte a él desde tu móvil o Google Calendar como si fuera el calendario de la F1 o los festivos.

## 🚀 Cómo funciona

1. Un script de Python (`update_calendar.py`) descarga los datos de la web de la federación.
2. Genera un archivo `cv_bunyola.ics` válido.
3. GitHub Actions ejecuta este script automáticamente cada día.
4. Tú te suscribes a la URL del archivo `.ics` una sola vez y recibes las actualizaciones automáticamente.

## 🛠️ Configuración (Solo una vez)

### 1. Crear repositorio en GitHub
1. Crea un nuevo repositorio público (ej: `calendario-voleibol`).
2. Sube los archivos: `update_calendar.py`, `requirements.txt` y `.github/workflows/update.yml`.

### 2. Activar la actualización automática
1. Ve a la pestaña **Actions** de tu repositorio.
2. Si ves un aviso, habilita los workflows.
3. Selecciona "Actualizar Calendario" en la izquierda y dale a **Run workflow** para generar el calendario por primera vez.

### 3. Obtener el enlace de suscripción
1. Una vez ejecutado, aparecerá un archivo `cv_bunyola.ics` en la lista de archivos.
2. Haz clic en él y luego en el botón **Raw**.
3. Copia esa URL. Debería ser algo así:
   `https://raw.githubusercontent.com/TU_USUARIO/calendario-voleibol/main/cv_bunyola.ics`

---

## 📅 Cómo suscribirse

### En iPhone / iPad
1. Ve a **Ajustes** > **Calendario** > **Cuentas**.
2. **Añadir cuenta** > **Otras** > **Añadir calendario suscrito**.
3. Pega la URL del paso anterior.
4. Dale a Siguiente y Guardar.

### En Google Calendar (Android / Web)
1. Abre [Google Calendar](https://calendar.google.com) en el ordenador.
2. A la izquierda, junto a "Otros calendarios", haz clic en el `+`.
3. Selecciona **Desde URL**.
4. Pega la URL del paso anterior y haz clic en **Añadir calendario**.
   *(Nota: Google puede tardar hasta 12-24h en refrescar cambios, pero es automático)*.

### En Outlook / Windows
1. Ir a la vista de Calendario.
2. **Añadir calendario** > **Desde Internet**.
3. Pega la URL y ponle nombre.

---

## 🤖 Personalización

- **Frecuencia**: Edita `.github/workflows/update.yml` y cambia el cron `'0 8 * * *'` (ejecuta a las 8:00 UTC).
- **Competición**: Edita `COMPETITION_ID` en `update_calendar.py` para seguir a otro equipo.

