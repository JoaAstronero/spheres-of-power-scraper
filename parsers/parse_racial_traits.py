#!/usr/bin/env python3
"""
Spheres of Power Wiki - Parser de Rasgos Raciales Alternativos
--------------------------------------------------------------
Extrae los Alternate Racial Traits organizados por raza desde:
data/raw_html/options/magic_options/alternate-racial-traits.html
Guarda el resultado en:
data/json_layer2/races/alternate_racial_traits.json
"""

import json
import os
import re
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_FILE = os.path.join(BASE_DIR, "data", "raw_html", "options", "magic_options", "alternate-racial-traits.html")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "json_layer2", "races")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "alternate_racial_traits.json")

def clean_text(text):
    if not text:
        return ""
    return re.sub(r"[ \t]+", " ", text).strip()

def parse_alternate_racial_traits():
    if not os.path.exists(RAW_FILE):
        print(f"⚠️ Archivo no encontrado: {RAW_FILE}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(RAW_FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    content = soup.find("div", id="page-content") or soup.body

    races_data = {}
    current_race = None
    seen_traits = set()

    for el in content.find_all(["h1", "h2", "h3", "h4"]):
        text = clean_text(el.text)
        if not text or text in ["Spheres of Power Wiki", "A Quick Reference Site", "Special Release", "Table of Contents", "Links", "Systems"]:
            continue

        if el.name in ["h1", "h2"]:
            # Identificar nombre de raza base (ej. "Dwarf", "Elf", "Aasimar")
            race_name = text.split("(")[0].strip()
            current_race = race_name
            if current_race not in races_data:
                races_data[current_race] = {
                    "race_name": current_race,
                    "traits": []
                }
        elif el.name in ["h3", "h4"] and current_race:
            raw_title = text
            if raw_title in seen_traits:
                continue
            seen_traits.add(raw_title)

            clean_name = re.sub(r"\[.*?\]|\(.*?\)", "", raw_title).strip()
            source = "Core / Spheres"

            # Extraer descripción completa
            desc_parts = []
            curr = el.find_next_sibling()
            while curr and curr.name not in ["h1", "h2", "h3", "h4", "hr"]:
                if curr.name in ["p", "blockquote", "div"]:
                    pt = clean_text(curr.text)
                    if pt.startswith("Source:"):
                        source = pt
                    elif pt:
                        desc_parts.append(pt)
                elif curr.name in ["ul", "ol"]:
                    items = [clean_text(li.text) for li in curr.find_all("li") if clean_text(li.text)]
                    if items:
                        desc_parts.append("\n".join(f"• {item}" for item in items))
                curr = curr.find_next_sibling()

            full_desc = "\n\n".join(desc_parts)

            # Detectar qué rasgo reemplaza
            replaces_match = re.search(r"(?:This replaces|This modifies|Replaces|Modifies)\s+([^.]+)", full_desc, re.I)
            replaces_text = clean_text(replaces_match.group(1)) if replaces_match else None

            # Detectar bonos de características en la descripción
            ability_mods = {}
            if re.search(r"\+2 (?:to )?strength", full_desc, re.I): ability_mods["str"] = 2
            if re.search(r"\+2 (?:to )?dexterity", full_desc, re.I): ability_mods["dex"] = 2
            if re.search(r"\+2 (?:to )?constitution", full_desc, re.I): ability_mods["con"] = 2
            if re.search(r"\+2 (?:to )?intelligence", full_desc, re.I): ability_mods["int"] = 2
            if re.search(r"\+2 (?:to )?wisdom", full_desc, re.I): ability_mods["wis"] = 2
            if re.search(r"\+2 (?:to )?charisma", full_desc, re.I): ability_mods["cha"] = 2

            races_data[current_race]["traits"].append({
                "id": f"trait_{clean_name.lower().replace(' ', '_')}",
                "name": clean_name,
                "raw_heading": raw_title,
                "source": source,
                "replaces": replaces_text,
                "ability_modifiers": ability_mods,
                "description": full_desc
            })

    # Guardar JSON consolidado
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(races_data, f, indent=2, ensure_ascii=False)

    total_traits = sum(len(r["traits"]) for r in races_data.values())
    print(f"✅ Extracción completada: {len(races_data)} razas y {total_traits} rasgos raciales alternativos.")
    print(f"📄 Guardado en: {OUTPUT_FILE}")

if __name__ == "__main__":
    parse_alternate_racial_traits()
