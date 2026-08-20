#!/usr/bin/env python3
"""
Spheres of Power Wiki — Parser de Tradiciones Mágicas y Marciales (Capa 2 Pulido)
----------------------------------------------------------------------------------
"""

import json
import os
import re
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPTIONS_DIR = os.path.join(BASE_DIR, "data", "raw_html", "options")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "json_layer2", "traditions")

def clean_text(text):
    if not text:
        return ""
    return re.sub(r"[ \t]+", " ", text).strip()

def parse_casting_traditions():
    html_path = os.path.join(OPTIONS_DIR, "magic_options", "casting-traditions.html")
    if not os.path.exists(html_path):
        print(f"⚠️ No se encontró {html_path}")
        return None

    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    page_content = soup.find("div", id="page-content")
    if not page_content:
        return None

    drawbacks = []
    boons = []
    sample_traditions = []
    
    current_section = "general_drawbacks"
    current_sphere_scope = "Universal"

    for el in page_content.find_all(["h1", "h2", "h3", "h4"]):
        h_text = clean_text(el.text)
        h_lower = h_text.lower()

        if el.name in ["h1", "h2"]:
            if "general drawback" in h_lower:
                current_section = "general_drawbacks"
                current_sphere_scope = "Universal"
            elif "sphere-specific drawback" in h_lower or "sphere specific" in h_lower:
                current_section = "sphere_drawbacks"
            elif "boon" in h_lower:
                current_section = "boons"
                current_sphere_scope = "Universal"
            elif "sample tradition" in h_lower or "traditions" in h_lower:
                current_section = "sample_traditions"
        elif el.name == "h3" and current_section == "sphere_drawbacks":
            current_sphere_scope = h_text
        elif el.name in ["h3", "h4"]:
            item_name = h_text
            if not item_name or item_name.lower().startswith("table of contents") or item_name.lower() in ["special release", "links", "systems"]:
                continue

            desc_parts = []
            curr = el.find_next_sibling()
            while curr and curr.name not in ["h1", "h2", "h3", "h4", "hr"]:
                if curr.name in ["p", "blockquote", "div"]:
                    pt = clean_text(curr.text)
                    if pt and not pt.startswith("Source:"):
                        desc_parts.append(pt)
                elif curr.name in ["ul", "ol"]:
                    items = [clean_text(li.text) for li in curr.find_all("li") if clean_text(li.text)]
                    if items:
                        desc_parts.append("\n".join(f"• {it}" for it in items))
                curr = curr.find_next_sibling()

            full_desc = "\n\n".join(desc_parts)

            entry = {
                "name": item_name,
                "scope": current_sphere_scope if current_section == "sphere_drawbacks" else "Universal",
                "description": full_desc
            }

            if current_section in ["general_drawbacks", "sphere_drawbacks"]:
                drawbacks.append(entry)
            elif current_section == "boons":
                boons.append(entry)
            elif current_section == "sample_traditions":
                sample_traditions.append(entry)

    return {
        "title": "Casting Traditions",
        "description": "Reglas para personalizar y definir el método de lanzamiento mágico mediante Drawbacks y Boons.",
        "ability_modifiers": ["Intelligence", "Wisdom", "Charisma"],
        "base_rule": "Ganas 2 talentos mágicos iniciales. Cada Drawback general otorga 1 punto de hechizo adicional (+1 SP por cada 3 niveles) o talentos específicos.",
        "total_drawbacks": len(drawbacks),
        "total_boons": len(boons),
        "total_sample_traditions": len(sample_traditions),
        "drawbacks": drawbacks,
        "boons": boons,
        "sample_traditions": sample_traditions
    }

def parse_martial_traditions():
    html_path = os.path.join(OPTIONS_DIR, "martial_options", "martial-traditions.html")
    if not os.path.exists(html_path):
        print(f"⚠️ No se encontró {html_path}")
        return None

    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    page_content = soup.find("div", id="page-content")
    if not page_content:
        return None

    sample_traditions = []
    for h in page_content.find_all(["h3", "h4"]):
        t_name = clean_text(h.text)
        if not t_name or t_name.lower().startswith("table of contents"):
            continue

        desc_parts = []
        curr = h.find_next_sibling()
        while curr and curr.name not in ["h1", "h2", "h3", "h4", "hr"]:
            if curr.name in ["p", "blockquote", "div", "ul"]:
                pt = clean_text(curr.text)
                if pt and not pt.startswith("Source:"):
                    desc_parts.append(pt)
            curr = curr.find_next_sibling()

        sample_traditions.append({
            "name": t_name,
            "description": "\n\n".join(desc_parts)
        })

    return {
        "title": "Martial Traditions",
        "description": "Reglas para definir el trasfondo marcial y proficiencias de armas/armaduras de un combatiente de esferas.",
        "key_ability_modifiers": ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"],
        "base_rule": "Ganas el paquete Equipment Sphere y 2 talentos marciales iniciales de tu elección o de una tradición preconstruida.",
        "total_sample_traditions": len(sample_traditions),
        "sample_traditions": sample_traditions
    }

def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("📜 Parseando Tradiciones Mágicas...")
    casting_data = parse_casting_traditions()
    if casting_data:
        out_file = os.path.join(OUTPUT_DIR, "casting_traditions.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(casting_data, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Casting Traditions: {casting_data['total_drawbacks']} Drawbacks, {casting_data['total_boons']} Boons, {casting_data['total_sample_traditions']} Tradiciones de muestra.")

    print("⚔️ Parseando Tradiciones Marciales...")
    martial_data = parse_martial_traditions()
    if martial_data:
        out_file = os.path.join(OUTPUT_DIR, "martial_traditions.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(martial_data, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Martial Traditions: {martial_data['total_sample_traditions']} Tradiciones marciales extraídas.")

    print(f"\n🎉 ¡Procesamiento de tradiciones completado! Guardadas en {OUTPUT_DIR}")

if __name__ == "__main__":
    run()
