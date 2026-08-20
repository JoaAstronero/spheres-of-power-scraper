#!/usr/bin/env python3
"""
Spheres of Power Wiki - Parser de Clases (Capa 2)
-------------------------------------------------
Procesa los archivos HTML de clases en data/raw_html/classes/ y extrae:
- Nombre y tipo de clase (Spherecaster, Practitioner, Champion, etc.)
- Dado de Golpe (Hit Die) y Rangos de Habilidad
- Tabla de progresión BAB, Fort, Ref, Will y Habilidades Especiales (Niveles 1-20)
- Rasgos de clase (Class Features) y especializaciones
- Referencias cruzadas a arquetipos
Guarda los JSONs en data/json_layer2/classes/.
"""

import glob
import json
import os
import re
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_CLASSES_DIR = os.path.join(BASE_DIR, "data", "raw_html", "classes")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "json_layer2", "classes")

def clean_text(text):
    if not text:
        return ""
    return re.sub(r"[ \t]+", " ", text).strip()

def parse_class_file(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    title_el = soup.find("div", id="page-title")
    class_name = clean_text(title_el.text) if title_el else os.path.splitext(os.path.basename(html_path))[0].capitalize()

    page_content = soup.find("div", id="page-content")
    if not page_content:
        return None

    # Detectar categoría según el subdirectorio (spherecasters, practitioners, champions, etc.)
    subfolder = os.path.basename(os.path.dirname(html_path))

    # Extraer Hit Die y Rangos de Habilidad
    full_text = page_content.text
    hd_match = re.search(r"Hit Die:\s*(d\d+)", full_text, re.IGNORECASE)
    skills_match = re.search(r"Skill Ranks (?:at Each Level|per Level):\s*([0-9\s\+A-Za-z]+(?:\.|\n))", full_text, re.IGNORECASE)
    
    hit_die = hd_match.group(1) if hd_match else "Unknown"
    skill_ranks = skills_match.group(1).strip(". \n") if skills_match else "Unknown"

    # Extraer Tabla de Progresión
    progression = []
    for table in page_content.find_all("table"):
        headers = [clean_text(th.text).lower() for th in table.find_all("th")]
        if any("level" in h for h in headers) and any("base attack" in h or "bab" in h for h in headers):
            rows = table.find_all("tr")[1:] # Omitir fila de encabezados
            for r in rows:
                cols = [clean_text(td.text) for td in r.find_all(["td", "th"])]
                if len(cols) >= 5:
                    progression.append({
                        "level": cols[0],
                        "bab": cols[1],
                        "fort": cols[2],
                        "ref": cols[3],
                        "will": cols[4],
                        "special": cols[5] if len(cols) > 5 else ""
                    })
            if progression:
                break

    # Extraer Rasgos de Clase (Class Features)
    features = []
    for h in page_content.find_all(["h2", "h3", "h4"]):
        if h.find_parent("div", id="toc"):
            continue
        h_name = clean_text(h.text)
        if not h_name or h_name.lower() in ["class features", "table of contents", "archetypes", "special release"]:
            continue

        desc_parts = []
        curr = h.find_next_sibling()
        while curr and curr.name not in ["h1", "h2", "h3", "h4", "hr"]:
            if curr.name in ["p", "blockquote", "div"]:
                t = clean_text(curr.text)
                if t and not t.startswith("Source:"):
                    desc_parts.append(t)
            elif curr.name in ["ul", "ol"]:
                items = [clean_text(li.text) for li in curr.find_all("li") if clean_text(li.text)]
                if items:
                    desc_parts.append("\n".join(f"• {item}" for item in items))
            curr = curr.find_next_sibling()

        features.append({
            "name": h_name,
            "description": "\n\n".join(desc_parts)
        })

    # Referencias cruzadas a arquetipos
    archetypes_list = []
    for h in page_content.find_all(["h1", "h2", "h3"]):
        if "archetype" in clean_text(h.text).lower():
            next_el = h.find_next_sibling(["p", "ul", "table"])
            if next_el:
                for a in next_el.find_all("a"):
                    txt = clean_text(a.text)
                    if txt and txt not in archetypes_list:
                        archetypes_list.append(txt)

    return {
        "class_name": class_name,
        "category": subfolder,
        "source_file": os.path.basename(html_path),
        "hit_die": hit_die,
        "skill_ranks_per_level": skill_ranks,
        "progression_table": progression,
        "total_features": len(features),
        "features": features,
        "associated_archetypes": archetypes_list
    }

def process_all_classes():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    html_files = glob.glob(os.path.join(RAW_CLASSES_DIR, "**", "*.html"), recursive=True)

    if not html_files:
        print(f"⚠️ No se encontraron archivos HTML en {RAW_CLASSES_DIR}.")
        return

    print(f"🔄 Procesando {len(html_files)} clases a Capa 2 (JSON)...")
    success_count = 0

    for html_file in sorted(html_files):
        data = parse_class_file(html_file)
        if data:
            slug = os.path.splitext(os.path.basename(html_file))[0]
            out_file = os.path.join(OUTPUT_DIR, f"{slug}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            success_count += 1
            print(f"  ✅ {data['class_name']:20} [{data['category']:14}] -> HD: {data['hit_die']:4} | Niveles: {len(data['progression_table']):2} | Rasgos: {data['total_features']:2}")

    print(f"\n🎉 ¡Procesamiento de clases completado! {success_count} clases guardadas en: {OUTPUT_DIR}")

if __name__ == "__main__":
    process_all_classes()
