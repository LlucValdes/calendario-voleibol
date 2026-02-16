import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
import datetime
import re
import pytz
import time
import json

# --- CONFIGURACIÓN ---
URL_BASE = "https://www.voleibolib.net/JSON/get_resultados.asp?id=7946&jor={}"
OUTPUT_FILE_ICS = 'cv_bunyola.ics'
OUTPUT_FILE_JSON = 'matches.json'
TEAM_NAME = "BUNYOLA"

# Definimos zonas horarias explícitas
TZ_MADRID = pytz.timezone('Europe/Madrid')
TZ_UTC = pytz.utc



def get_matches():
    print(f"🔄 Descargando datos y convirtiendo a UTC estricto...")
    matches = []
    jor = 1
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://www.voleibolib.net/'
    }

    while True:
        url = URL_BASE.format(jor)
        print(f"   Inspecionando Jornada {jor}...", end="\r")
        
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"\n❌ Error HTTP {resp.status_code} en Jornada {jor}")
                break
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            match_divs = soup.find_all('div', class_='info_partido')
            
            # Si no hay partidos, asumimos que hemos terminado
            if not match_divs:
                # Doble check: a veces devuelve un HTML vacío o con error
                if "JORNADA" not in resp.text: 
                     print(f"\n🏁 Fin de datos detectado en Jornada {jor} (sin contenido).")
                     break
                # Si hay texto de Jornada pero 0 partidos, igual seguimos por si acaso es una jornada de descanso?
                # Pero la estructura usual es que si no hay info_partido, no hay partidos mostrados.
                # Probaremos a parar.
                print(f"\n🏁 Fin de datos detectado en Jornada {jor} (0 partidos).")
                break

            for div in match_divs:
                # 1. Check if our team is playing
                full_text = div.get_text(" ", strip=True).upper()
                if TEAM_NAME not in full_text:
                    continue

                # 2. Extract Data
                fecha_span = div.find('span', class_='fecha')
                pabellon_span = div.find('span', class_='pabellon')
                table = div.find('table')
                
                if not fecha_span or not table:
                    continue
                    
                fecha_str_raw = fecha_span.get_text(strip=True) # Ex: "12/10/2025 - 12:00"
                ubicacion = pabellon_span.get_text(strip=True) if pabellon_span else "Consultar web"
                
                # Parse Teams & Result
                # Table usually has one row with columns: Local | Result | Visitor
                rows = table.find_all('tr')
                found_match_row = False
                local = "Unknown"
                visitante = "Unknown"
                resultado = ""
                
                for row in rows:
                    cols = row.find_all('td')
                    # We expect at least 3 cols for a valid match row layout
                    if len(cols) >= 3:
                        # Extract text from columns
                        c0 = cols[0].get_text(strip=True)
                        c1 = cols[1].get_text(strip=True)
                        c2 = cols[2].get_text(strip=True)
                        
                        # Verify this looks like the match row
                        if c0 and c2: 
                            local = c0
                            visitante = c2
                            resultado = c1 # e.g. "3 - 0" or "vs" or empty
                            found_match_row = True
                            break
                
                if not found_match_row: 
                    continue


                # Parse Date
                fecha_str = ""
                hora_str = "00:00"
                all_day = True
                
                # Try parsing "dd/mm/yyyy - HH:MM"
                try:
                    if " - " in fecha_str_raw:
                        parts = fecha_str_raw.split(" - ")
                        fecha_str = parts[0].strip()
                        hora_str = parts[1].strip()
                        all_day = False
                    else:
                        fecha_str = fecha_str_raw.strip()
                        
                    # Build datetime
                    if all_day:
                         begin = datetime.datetime.strptime(fecha_str, "%d/%m/%Y").date()
                    else:
                        dt_naive = datetime.datetime.strptime(f"{fecha_str} {hora_str}", "%d/%m/%Y %H:%M")
                        dt_madrid = TZ_MADRID.localize(dt_naive)
                        begin = dt_madrid.astimezone(TZ_UTC)
                        
                    matches.append({
                        'name': f"🏐 {local} vs {visitante}",
                        'begin': begin,
                        'all_day': all_day,
                        'description': f"Jornada {jor}\nResultado: {resultado}",
                        'location': ubicacion,
                        'uid': f"bunyola-match-jornada-{jor}@voleibolib.net"
                    })
                    
                except ValueError as ve:
                    print(f"\n⚠️ Error fecha '{fecha_str_raw}': {ve}")
                    continue

        except Exception as e:
            print(f"\n❌ Error procesando Jornada {jor}: {e}")
            
        jor += 1
        # Pequeña pausa para no saturar 
        time.sleep(0.2)

    print(f"\n✅ Total partidos encontrados: {len(matches)}")
    return matches

def generate_ics(matches):
    if not matches: 
        print("⚠️ No hay partidos para guardar.")
        return

    c = Calendar()
    for m in matches:
        e = Event()
        e.name = m['name']
        e.begin = m['begin']
        e.uid = m['uid']
        
        if m['all_day']:
            e.make_all_day()
        else:
            e.duration = datetime.timedelta(hours=2)
            
        e.description = m['description'] + "\n\nActualizado autom. vía Voleibolib"
        e.location = m['location']
        c.events.add(e)
        
    # Serialize and inject custom calendar name
    lines = list(c.serialize_iter())
    # Insert X-WR-CALNAME after the first line (BEGIN:VCALENDAR) or wherever appropriate
    # Usually after VERSION or PRODID is fine. We'll put it early.
    lines.insert(1, "X-WR-CALNAME:CV Bunyola\n")
    
    with open(OUTPUT_FILE_ICS, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✅ Calendario generado correctamente: {OUTPUT_FILE_ICS}")

def save_json(matches):
    """Saves matches to a JSON file for external consumption (Google Apps Script)."""
    if not matches:
        return

    # Convert datetime objects to strings for JSON serialization
    serializable_matches = []
    for m in matches:
        match_dict = m.copy()
        # Convert date/datetime to ISO string
        if isinstance(match_dict['begin'], (datetime.date, datetime.datetime)):
            match_dict['begin'] = match_dict['begin'].isoformat()
        
        serializable_matches.append(match_dict)

    with open(OUTPUT_FILE_JSON, 'w', encoding='utf-8') as f:
        json.dump(serializable_matches, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON generado correctamente: {OUTPUT_FILE_JSON}")

if __name__ == "__main__":
    data = get_matches()
    generate_ics(data)
    save_json(data)
