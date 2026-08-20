#!/usr/bin/env python3
"""
Spheres of Power Wiki - Parser Universal de Esferas (Capa 2 Pulido)
--------------------------------------------------------------------
Extrae talentos y reglas con soporte para párrafos, listas (ul/ol) y tablas.
"""

import argparse
import glob
import json
import os
import re
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_SPHERES_DIR = os.path.join(BASE_DIR, "data", "raw_html", "spheres")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "json_layer2", "spheres")

def clean_text(text):
    if not text:
        return ""
    return re.sub(r"[ \t]+", " ", text).strip()

def parse_sub_traits(paragraphs):
    """Extrae sub-traits cuando un elemento comienza con negrita o encabezado de sub-rasgo."""
    clean_paragraphs = []
    sub_traits = []
    
    for p in paragraphs:
        # Detectar líneas tipo "Trait Name: Effect description..."
        match = re.match(r"^([A-Z][A-Za-z0-9\s,\/’'-]+?)[:.-]\s+(.+)$", p)
        if match and len(match.group(1).split()) <= 4:
            sub_traits.append({
                "name": match.group(1).strip(),
                "effect": match.group(2).strip()
            })
        else:
            clean_paragraphs.append(p)
            
    return clean_paragraphs, sub_traits

def extract_box_content(box):
    """Extrae párrafos, listas y tablas preservando la estructura."""
    paragraphs = []
    source = "Core / Ultimate"
    
    for child in box.children:
        if not hasattr(child, "name") or not child.name:
            continue
        if child.name in ["h3", "h4", "h5"]:
            continue
        if child.name == "sup" or (child.name == "p" and child.text.strip().startswith("Source:")):
            source = clean_text(child.text)
            continue
        if child.name in ["p", "blockquote", "div"]:
            txt = clean_text(child.text)
            if txt and not txt.startswith("Source:"):
                paragraphs.append(txt)
        elif child.name in ["ul", "ol"]:
            items = [clean_text(li.text) for li in child.find_all("li") if clean_text(li.text)]
            if items:
                paragraphs.append("\n".join(f"• {item}" for item in items))
        elif child.name == "table":
            # Extraer tabla simple
            rows = []
            for tr in child.find_all("tr"):
                cells = [clean_text(td.text) for td in tr.find_all(["td", "th"])]
                if cells:
                    rows.append(" | ".join(cells))
            if rows:
                paragraphs.append("\n".join(rows))

    desc_ps, sub_traits = parse_sub_traits(paragraphs)
    return "\n\n".join(desc_ps), sub_traits, source

def parse_sphere_file(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    page_title = soup.find("div", id="page-title")
    sphere_name = clean_text(page_title.text) if page_title else os.path.splitext(os.path.basename(html_path))[0].capitalize()

    page_content = soup.find("div", id="page-content")
    if not page_content:
        return None

    # Si hay pestañas (Ultimate vs Original), usamos la pestaña Ultimate (tab-0-0)
    tabs = page_content.find_all("div", id=lambda x: x and x.startswith("wiki-tab-"))
    active_container = tabs[0] if tabs else page_content

    talents = []
    seen_headings = set()

    # Estrategia 1: Cajas con borde negro (Esferas Mágicas)
    boxes = active_container.find_all("div", style=lambda s: s and "border: 1px solid black" in s)

    if boxes:
        for box in boxes:
            h4 = box.find(["h4", "h3", "h5"])
            if not h4:
                continue
            raw_heading = clean_text(h4.text)
            if raw_heading in seen_headings or not raw_heading:
                continue
            seen_headings.add(raw_heading)
            
            tag_matches = re.findall(r"\[(.*?)\]|\((.*?)\)", raw_heading)
            tags = [m[0] or m[1] for m in tag_matches if m[0] or m[1]]
            clean_name = re.sub(r"\[.*?\]|\(.*?\)", "", raw_heading).strip()

            desc, sub_traits, source = extract_box_content(box)

            talents.append({
                "name": clean_name,
                "raw_heading": raw_heading,
                "tags": tags,
                "source": source,
                "description": desc,
                "sub_traits": sub_traits
            })

    # Estrategia 2: Encabezados <h4> libres (Esferas de Combate y Habilidad)
    if not talents:
        for h4 in active_container.find_all(["h4", "h3"]):
            if h4.find_parent("div", id="toc"):
                continue
            
            raw_heading = clean_text(h4.text)
            if not raw_heading or "table of contents" in raw_heading.lower() or raw_heading.lower() in ["special release", "links", "systems"]:
                continue
            if raw_heading in seen_headings:
                continue
            seen_headings.add(raw_heading)

            tag_matches = re.findall(r"\[(.*?)\]|\((.*?)\)", raw_heading)
            tags = [m[0] or m[1] for m in tag_matches if m[0] or m[1]]
            clean_name = re.sub(r"\[.*?\]|\(.*?\)", "", raw_heading).strip()

            paragraphs = []
            source = "Core / Ultimate"

            curr = h4.find_next_sibling()
            while curr and curr.name not in ["h1", "h2", "h3", "h4", "hr"]:
                if curr.name in ["p", "div", "blockquote"]:
                    pt = clean_text(curr.text)
                    if pt.startswith("Source:"):
                        source = pt
                    elif pt:
                        paragraphs.append(pt)
                elif curr.name in ["ul", "ol"]:
                    items = [clean_text(li.text) for li in curr.find_all("li") if clean_text(li.text)]
                    if items:
                        paragraphs.append("\n".join(f"• {item}" for item in items))
                curr = curr.find_next_sibling()

            desc_ps, sub_traits = parse_sub_traits(paragraphs)

            talents.append({
                "name": clean_name,
                "raw_heading": raw_heading,
                "tags": tags,
                "source": source,
                "description": "\n\n".join(desc_ps),
                "sub_traits": sub_traits
            })

    # Extraer referencias cruzadas
    associated_feats = []
    associated_archetypes = []
    for h in active_container.find_all(["h1", "h2", "h3"]):
        h_text = clean_text(h.text).lower()
        if "feat" in h_text:
            next_el = h.find_next_sibling(["p", "ul", "table"])
            if next_el:
                for a in next_el.find_all("a"):
                    txt = clean_text(a.text)
                    if txt:
                        associated_feats.append(txt)
        elif "archetype" in h_text:
            next_el = h.find_next_sibling(["p", "ul", "table"])
            if next_el:
                for a in next_el.find_all("a"):
                    txt = clean_text(a.text)
                    if txt:
                        associated_archetypes.append(txt)

    return {
        "sphere_name": sphere_name,
        "source_file": os.path.basename(html_path),
        "total_talents": len(talents),
        "talents": talents,
        "cross_references": {
            "associated_feats": list(dict.fromkeys(associated_feats)),
            "associated_archetypes": list(dict.fromkeys(associated_archetypes))
        }
    }

def process_all_spheres():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    html_files = glob.glob(os.path.join(RAW_SPHERES_DIR, "**", "*.html"), recursive=True)

    if not html_files:
        print(f"⚠️ No se encontraron archivos HTML en {RAW_SPHERES_DIR}.")
        return

    print(f"🔄 Procesando {len(html_files)} esferas a Capa 2 (JSON)...")
    total_talents_all = 0

    for html_file in sorted(html_files):
        data = parse_sphere_file(html_file)
        if data:
            slug = os.path.splitext(os.path.basename(html_file))[0]
            out_file = os.path.join(OUTPUT_DIR, f"{slug}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            total_talents_all += data['total_talents']

    print(f"🎉 Total de talentos extraídos en todas las esferas: {total_talents_all}")
    print(f"📁 Directorio de salida: {OUTPUT_DIR}")

if __name__ == "__main__":
    process_all_spheres()
