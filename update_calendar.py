import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
import datetime
import re
import pytz

# --- CONFIGURACIÓN ---
URL_DATOS = "https://www.voleibolib.net/JSON/get_calendario.asp?id=7946"
OUTPUT_FILE = 'cv_bunyola.ics'

# Definimos zonas horarias explícitas
TZ_MADRID = pytz.timezone('Europe/Madrid')
TZ_UTC = pytz.utc

PABELLONES_CONOCIDOS = {
    "SCANNER CV SON FERRER": "Pabellón Son Ferrer (Calvià)",
    "CASA NOVA VOLEI MURO": "Poliesportiu Municipal de Muro",
    "RAFAL VELL": "Poliesportiu Germans Escalas",
    "PALMA ESPORTS": "Poliesportiu Cide",
    "VIAJES LLABRES CV. PÒRTOL": "Pabellón Blanquerna",
    "ES CRUCE CV MANACOR": "Na Capellera (Manacor)",
    "CV CIUTADELLA BIOSPORT": "Poliesportiu Municipal Ciutadella",
    "CLUB VOLEI ES CASTELL": "Zona Esportiva Sergi Llull",
    "MAYURQA VOLEY PALMA": "Pabellón UIB",
    "ANAYA MAYURQA VOLEY PALMA": "Pabellón UIB",
    "CVS BAR SON ANGELATS SOLLER": "Pabellón Son Angelats (Sóller)",
    "C.V. BUNYOLA": "Escola Mestre Colom (Bunyola)" 
}

def get_matches():
    print(f"🔄 Descargando datos y convirtiendo a UTC estricto...")
    matches = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.voleibolib.net/'
        }
        
        resp = requests.get(URL_DATOS, headers=headers, timeout=15)
        if resp.status_code != 200: return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        tablas = soup.find_all('table', class_='calendario-completo')
        
        for tabla in tablas:
            th = tabla.find('th')
            titulo_jornada = th.get_text(strip=True) if th else "Jornada ?"
            
            for fila in tabla.find_all('tr'):
                if 'jornada' in fila.get('class', []): continue
                
                texto = fila.get_text(" ", strip=True)
                if "BUNYOLA" not in texto.upper(): continue
                
                cols = fila.find_all('td')
                if len(cols) < 3: continue
                
                local = cols[0].get_text(strip=True)
                visitante = cols[1].get_text(strip=True)
                info = cols[2]
                
                fecha_str = ""
                hora_str = "00:00"
                all_day = True
                resultado = ""
                
                strong = info.find('strong')
                if strong:
                    contenido = strong.get_text(" ", strip=True)
                    m_date = re.search(r'(\d{2}/\d{2}/\d{4})', contenido)
                    if m_date: fecha_str = m_date.group(1)
                    m_time = re.search(r'(\d{2}:\d{2})', contenido)
                    if m_time:
                        hora_str = m_time.group(1)
                        all_day = False
                else:
                    span_res = info.find('span', class_='resultado')
                    if span_res:
                        resultado = span_res.get_text(strip=True)
                        m_jor = re.search(r'(\d{2}/\d{2}/\d{4})', titulo_jornada)
                        if m_jor: fecha_str = m_jor.group(1)

                if not fecha_str: continue

                # Pabellón
                ubicacion = "Consultar web oficial"
                local_upper = local.upper().strip()
                for k, v in PABELLONES_CONOCIDOS.items():
                    if k in local_upper or local_upper in k:
                        ubicacion = v
                        break
                
                try:
                    if all_day:
                        # Eventos todo el día son date objects
                        begin = datetime.datetime.strptime(fecha_str, "%d/%m/%Y").date()
                    else:
                        # 1. Crear fecha "naive"
                        dt_naive = datetime.datetime.strptime(f"{fecha_str} {hora_str}", "%d/%m/%Y %H:%M")
                        
                        # 2. Localizarla en Madrid (esto le da la info de +1 o +2 según verano/invierno)
                        dt_madrid = TZ_MADRID.localize(dt_naive)
                        
                        # 3. CONVERTIR A UTC (ZULU)
                        # Esto es clave: guardamos el evento en hora universal
                        begin = dt_madrid.astimezone(TZ_UTC)
                    
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
    if not matches: return

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
    
    print(f"✅ Calendario generado correctamente en UTC.")

if __name__ == "__main__":
    data = get_matches()
    generate_ics(data)
