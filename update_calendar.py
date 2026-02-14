import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
import datetime
import re

# --- CONFIGURACIÓN ---
# Usamos la URL "secreta" que carga los datos (la del AJAX)
URL_DATOS = "https://www.voleibolib.net/JSON/get_calendario.asp?id=7946"
OUTPUT_FILE = 'cv_bunyola.ics'

# Diccionario de Pabellones (Tu seguro de vida para las ubicaciones)
PABELLONES_CONOCIDOS = {
    "SCANNER CV SON FERRER": "Pav. IES Son Ferrer",
    "CASA NOVA VOLEI MURO": "Pav. IES Sta. Margalida",
    "RAFAL VELL": "Poliesportiu Germans Escalas",
    "PALMA ESPORTS": "Poliesportiu Cide",
    "VIAJES LLABRES CV. PÒRTOL": "Pabellón Blanquerna",
    "ES CRUCE CV MANACOR": "Na Capellera (Manacor)",
    "CV CIUTADELLA BIOSPORT": "Poliesportiu Municipal Ciutadella",
    "CLUB VOLEI ES CASTELL": "Zona Esportiva Sergi Llull",
    "MAYURQA VOLEY PALMA": "Pol. Germans Escales",
    "ANAYA MAYURQA VOLEY PALMA": "Pabellón UIB",
    "CVS BAR SON ANGELATS SOLLER": "Pabellón Son Angelats (Sóller)",
    "C.V. BUNYOLA": "Pav. Juan Pericas Riera" 
}

def get_matches():
    print(f"🔄 Descargando datos desde la API oculta...")
    matches = []
    
    try:
        # Cabeceras anti-bloqueo
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.voleibolib.net/'
        }
        
        # 1. Petición a la URL que devuelve las TABLAS (HTML puro)
        resp = requests.get(URL_DATOS, headers=headers, timeout=15)
        
        if resp.status_code != 200:
            print(f"❌ Error HTTP {resp.status_code}")
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 2. Buscar todas las tablas de jornadas
        tablas = soup.find_all('table', class_='calendario-completo')
        print(f"ℹ️ Se encontraron {len(tablas)} jornadas con datos.")
        
        for tabla in tablas:
            # Título: "Jornada 1 11/10/2025"
            th = tabla.find('th')
            titulo_jornada = th.get_text(strip=True) if th else "Jornada ?"
            
            # Filas de partidos
            filas = tabla.find_all('tr')
            for fila in filas:
                # Saltamos encabezados
                if 'jornada' in fila.get('class', []): continue
                
                texto = fila.get_text(" ", strip=True)
                
                # FILTRO: Solo Bunyola
                if "BUNYOLA" not in texto.upper(): continue
                
                cols = fila.find_all('td')
                if len(cols) < 3: continue
                
                # Columnas: [Local] [Visitante] [Resultado/Fecha]
                local = cols[0].get_text(strip=True)
                visitante = cols[1].get_text(strip=True)
                info = cols[2]
                
                # Datos por defecto
                fecha_str = ""
                hora_str = "00:00"
                all_day = True
                resultado = ""
                
                # Analizar columna de información
                strong = info.find('strong')
                if strong:
                    # Partido FUTURO: tiene <strong>Fecha<br>Hora</strong>
                    contenido = strong.get_text(" ", strip=True)
                    
                    m_date = re.search(r'(\d{2}/\d{2}/\d{4})', contenido)
                    if m_date: fecha_str = m_date.group(1)
                    
                    m_time = re.search(r'(\d{2}:\d{2})', contenido)
                    if m_time:
                        hora_str = m_time.group(1)
                        all_day = False
                else:
                    # Partido PASADO: tiene <span class="resultado">
                    span_res = info.find('span', class_='resultado')
                    if span_res:
                        resultado = span_res.get_text(strip=True)
                        # Usamos la fecha genérica del título de la jornada
                        m_jor = re.search(r'(\d{2}/\d{2}/\d{4})', titulo_jornada)
                        if m_jor: fecha_str = m_jor.group(1)

                if not fecha_str: continue

                # DEDUCIR PABELLÓN (Porque esta tabla no lo trae)
                ubicacion = "Consultar web oficial"
                local_upper = local.upper().strip()
                
                # Búsqueda aproximada en el diccionario
                for nombre_equipo, nombre_pabellon in PABELLONES_CONOCIDOS.items():
                    if nombre_equipo in local_upper or local_upper in nombre_equipo:
                        ubicacion = nombre_pabellon
                        break
                
                # Crear evento
                try:
                    if all_day:
                        begin = datetime.datetime.strptime(fecha_str, "%d/%m/%Y")
                    else:
                        begin = datetime.datetime.strptime(f"{fecha_str} {hora_str}", "%d/%m/%Y %H:%M")
                    
                    matches.append({
                        'name': f"🏐 {local} vs {visitante}",
                        'begin': begin,
                        'all_day': all_day,
                        'description': f"{titulo_jornada}\nResultado: {resultado}" if resultado else titulo_jornada,
                        'location': ubicacion
                    })
                except ValueError:
                    continue

        return matches

    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def generate_ics(matches):
    if not matches:
        print("⚠️ No se han encontrado partidos.")
        return

    c = Calendar()
    for m in matches:
        e = Event()
        e.name = m['name']
        e.begin = m['begin']
        if m['all_day']:
            e.make_all_day()
        else:
            e.duration = datetime.timedelta(hours=2)
            
        e.description = m['description'] + "\n\nActualizado autom."
        e.location = m['location']
        c.events.add(e)
        
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.writelines(c.serialize_iter())
    
    print(f"✅ Calendario generado: {OUTPUT_FILE} ({len(matches)} partidos)")

if __name__ == "__main__":
    data = get_matches()
    generate_ics(data)
