#!/usr/bin/env python3
"""
Spheres of Power Wiki - Parser de Arquetipos (Capa 2)
-----------------------------------------------------
Procesa los archivos HTML de arquetipos en data/raw_html/archetypes/ y extrae:
- Nombre del arquetipo y clase base asociada
- Fuente / Editorial
- Rasgos de clase reemplazados o modificados (para compatibilidad de arquetipos)
- Nuevas habilidades de clase otorgadas por el arquetipo
Guarda los JSONs en data/json_layer2/archetypes/.
"""

import glob
import json
import os
import re
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_ARCHETYPES_DIR = os.path.join(BASE_DIR, "data", "raw_html", "archetypes")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "json_layer2", "archetypes")

def clean_text(text):
    if not text:
        return ""
    return re.sub(r"[ \t]+", " ", text).strip()

def parse_archetype_file(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    title_el = soup.find("div", id="page-title")
    raw_name = clean_text(title_el.text) if title_el else os.path.splitext(os.path.basename(html_path))[0].capitalize()

    # Extraer clase base a partir del subdirectorio (ej. archetypes/alchemist -> Alchemist)
    base_class_folder = os.path.basename(os.path.dirname(html_path))
    base_class_name = base_class_folder.replace("_", " ").title()

    page_content = soup.find("div", id="page-content")
    if not page_content:
        return None

    # Extraer fuente
    sup = page_content.find("sup")
    source = clean_text(sup.text) if sup else "Core / Official"

    # Extraer rasgos del arquetipo
    features = []
    for h in page_content.find_all(["h2", "h3", "h4"]):
        if h.find_parent("div", id="toc"):
            continue
        h_name = clean_text(h.text)
        if not h_name or h_name.lower() in ["table of contents", "archetypes", "special release", "links", "systems"]:
            continue

        desc_parts = []
        replaces = []
        curr = h.find_next_sibling()
        while curr and curr.name not in ["h1", "h2", "h3", "h4", "hr"]:
            if curr.name in ["p", "blockquote", "div"]:
                t = clean_text(curr.text)
                if t and not t.startswith("Source:"):
                    desc_parts.append(t)
                    # Detectar cláusulas de reemplazo/modificación de habilidades
                    rep_matches = re.findall(r"(?:This (?:replaces|modifies|alters)|Replaces|Modifies)\s+([^\.]+)\.", t, re.IGNORECASE)
                    for rep in rep_matches:
                        clean_rep = clean_text(rep)
                        if clean_rep and clean_rep not in replaces:
                            replaces.append(clean_rep)
            elif curr.name in ["ul", "ol"]:
                items = [clean_text(li.text) for li in curr.find_all("li") if clean_text(li.text)]
                if items:
                    desc_parts.append("\n".join(f"• {item}" for item in items))
            curr = curr.find_next_sibling()

        features.append({
            "name": h_name,
            "replaces_or_modifies": replaces,
            "description": "\n\n".join(desc_parts)
        })

    return {
        "archetype_name": raw_name,
        "base_class": base_class_name,
        "source_file": os.path.basename(html_path),
        "source": source,
        "total_features": len(features),
        "features": features
    }

def process_all_archetypes():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    html_files = glob.glob(os.path.join(RAW_ARCHETYPES_DIR, "**", "*.html"), recursive=True)

    if not html_files:
        print(f"⚠️ No se encontraron archivos HTML en {RAW_ARCHETYPES_DIR}.")
        return

    print(f"🔄 Procesando {len(html_files)} arquetipos a Capa 2 (JSON)...")
    success_count = 0

    for html_file in sorted(html_files):
        data = parse_archetype_file(html_file)
        if data:
            slug = os.path.splitext(os.path.basename(html_file))[0]
            base_folder = os.path.basename(os.path.dirname(html_file))
            out_dir = os.path.join(OUTPUT_DIR, base_folder)
            os.makedirs(out_dir, exist_ok=True)
            out_file = os.path.join(out_dir, f"{slug}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            success_count += 1

    print(f"🎉 ¡Procesamiento de arquetipos completado! {success_count} arquetipos guardados en: {OUTPUT_DIR}")

if __name__ == "__main__":
    process_all_archetypes()
