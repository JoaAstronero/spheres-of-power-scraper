#!/usr/bin/env python3
"""
Spheres of Power Wiki - Manifest Generator
------------------------------------------
Este script extrae y clasifica todas las URLs clave de la página principal
de spheresofpower.wikidot.com y genera un archivo 'manifest.json' limpio y categorizado.
"""

import json
import os
import requests
from bs4 import BeautifulSoup

BASE_URL = "http://spheresofpower.wikidot.com"
MANIFEST_FILE = os.path.join(os.path.dirname(__file__), "manifest.json")

def get_clean_links(container):
    """Extrae enlaces únicos válidos omitiendo enlaces de sistema o vacíos."""
    seen = set()
    links = []
    for a in container.find_all("a", href=True):
        href = a["href"].strip()
        name = a.text.strip()
        if not href.startswith("/") or href.startswith(("/system:", "/forum:", "javascript:", "/#")):
            continue
        if href in ["/", "/about", "/contact", "/legal:start", "/start", "/archetype-rules"]:
            continue
        if not name:
            continue
        if href not in seen:
            seen.add(href)
            links.append({
                "name": name,
                "slug": href.lstrip("/"),
                "url": BASE_URL + href
            })
    return links

def parse_subsections_by_headings(div):
    """Parsea subsecciones dentro de un contenedor div basadas en <strong> o encabezados."""
    sections = {}
    current = "General"
    sections[current] = []
    
    for child in div.children:
        if child.name in ["p", "h2", "h3", "h4", "ul"]:
            strong = child.find("strong")
            if strong and len(strong.text.strip()) < 40 and not child.find("a"):
                current = strong.text.strip()
                if current not in sections:
                    sections[current] = []
            elif child.name in ["h2", "h3", "h4"] and not child.find("a"):
                current = child.text.strip()
                if current not in sections:
                    sections[current] = []
            else:
                links = get_clean_links(child)
                if current not in sections:
                    sections[current] = []
                sections[current].extend(links)
    return {k: v for k, v in sections.items() if v}

def extract_archetypes_by_class(div):
    """Extrae arquetipos agrupados por clase base desde el div de arquetipos."""
    archetypes_by_class = {}
    current_class = "General"

    for el in div.find_all(["strong", "a"]):
        if el.name == "strong":
            text = el.text.strip()
            if text and text != "Archetypes":
                current_class = text
                if current_class not in archetypes_by_class:
                    archetypes_by_class[current_class] = []
        elif el.name == "a":
            href = el.get("href", "").strip()
            name = el.text.strip()
            if href.startswith("/") and not href.startswith(("/system:", "/forum:", "javascript:", "/#")):
                if href not in ["/archetype-rules", "/"]:
                    if current_class not in archetypes_by_class:
                        archetypes_by_class[current_class] = []
                    archetypes_by_class[current_class].append({
                        "name": name,
                        "slug": href.lstrip("/"),
                        "url": BASE_URL + href
                    })
    return {k: v for k, v in archetypes_by_class.items() if v}

def generate_manifest():
    print(f"🌐 Descargando índice de {BASE_URL}...")
    headers = {"User-Agent": "SpheresManifestBuilder/1.0 (Educational/TTRPG)"}
    resp = requests.get(BASE_URL, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    content = soup.find("div", id="page-content")
    if not content:
        raise ValueError("No se pudo encontrar el elemento #page-content")

    divs = content.find_all("div", recursive=False)
    
    # 1. Esferas
    magic_spheres = parse_subsections_by_headings(divs[11]).get("Magic Spheres", [])
    combat_spheres = parse_subsections_by_headings(divs[13]).get("Combat Spheres", [])
    skill_spheres = parse_subsections_by_headings(divs[12]).get("Skill Spheres", [])

    # 2. Clases
    div14_sections = parse_subsections_by_headings(divs[14])
    div15_sections = parse_subsections_by_headings(divs[15])
    
    classes_spherecasters = div14_sections.get("Spherecasters", [])
    classes_prestige = div14_sections.get("Prestige Classes", [])
    classes_operatives = div15_sections.get("Operatives", [])
    classes_practitioners = div15_sections.get("Practitioners", [])
    classes_champions = div15_sections.get("Champions", [])

    # 3. Dotes y Opciones
    magic_options = parse_subsections_by_headings(divs[11]).get("Magic Options", [])
    feat_types = parse_subsections_by_headings(divs[11]).get("Feat Types", [])
    martial_options = parse_subsections_by_headings(divs[12]).get("Martial Options", [])
    skill_options = parse_subsections_by_headings(divs[12]).get("Skill Options", [])
    champion_options = parse_subsections_by_headings(divs[12]).get("Champion Options", [])

    # 4. Equipo y Objetos
    gear_items = parse_subsections_by_headings(divs[12]).get("Gear", [])
    practitioner_gear = parse_subsections_by_headings(divs[12]).get("Practitioner Gear", [])

    # 5. Arquetipos
    archetypes = extract_archetypes_by_class(divs[16])

    # Ensamblar estructura final del Manifest
    manifest = {
        "metadata": {
            "source": BASE_URL,
            "version": "Spheres of Power Wikidot Manifest 1.0",
            "total_categories": 7
        },
        "spheres": {
            "magic": magic_spheres,
            "combat": combat_spheres,
            "skill": skill_spheres
        },
        "classes": {
            "spherecasters": classes_spherecasters,
            "practitioners": classes_practitioners,
            "operatives": classes_operatives,
            "champions": classes_champions,
            "prestige": classes_prestige
        },
        "options_and_rules": {
            "magic_options": magic_options,
            "martial_options": martial_options,
            "skill_options": skill_options,
            "champion_options": champion_options,
            "feat_types": feat_types
        },
        "gear_and_items": {
            "general_gear": gear_items,
            "practitioner_gear": practitioner_gear
        },
        "archetypes_by_class": archetypes
    }

    # Calcular estadísticas
    all_urls = set()
    def count_urls(obj):
        if isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict) and "url" in item:
                    all_urls.add(item["url"])
        elif isinstance(obj, dict):
            for v in obj.values():
                count_urls(v)

    count_urls(manifest)

    manifest["metadata"]["total_unique_urls"] = len(all_urls)

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("\n✅ Manifest generado exitosamente:")
    print(f"   📁 Archivo: {MANIFEST_FILE}")
    print(f"   🔮 Esferas Mágicas: {len(magic_spheres)}")
    print(f"   ⚔️  Esferas de Combate: {len(combat_spheres)}")
    print(f"   🎭 Esferas de Habilidad (Skill): {len(skill_spheres)}")
    print(f"   🧙 Clases Base / Híbridas / Prestigio: {len(classes_spherecasters) + len(classes_practitioners) + len(classes_operatives) + len(classes_champions) + len(classes_prestige)}")
    print(f"   🛡️ Arquetipos clasificados: {sum(len(v) for v in archetypes.values())} (en {len(archetypes)} clases)")
    print(f"   📦 Objetos / Gear: {len(gear_items) + len(practitioner_gear)}")
    print(f"   🔗 Total URLs únicas catalogadas: {len(all_urls)}")

if __name__ == "__main__":
    generate_manifest()
