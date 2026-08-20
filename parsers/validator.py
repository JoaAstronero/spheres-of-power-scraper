#!/usr/bin/env python3
"""
Spheres of Power Wiki - Validador de Integridad (Capa 2)
--------------------------------------------------------
Audita la calidad de los JSONs generados por los parsers de esferas
y detecta anomalías, texto huérfano o estructuras especiales no capturadas.
Si una esfera falla la validación, señala qué necesita atención de un agente.
"""

import glob
import json
import os
import re
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw_html", "spheres")
JSON_DIR = os.path.join(BASE_DIR, "data", "json_layer2", "spheres")

# Reglas y heurísticas conocidas para esferas específicas
SPHERE_SPECIAL_REQUIREMENTS = {
    "destruction": {
        "required_tags": ["blast type", "blast shape"],
        "min_talents": 20
    },
    "alteration": {
        "required_tags": ["body", "transformation"],
        "min_talents": 30
    },
    "nature": {
        "min_talents": 25,
        "keywords": ["geomancy", "package"]
    },
    "creation": {
        "min_talents": 20
    },
    "dark": {
        "min_talents": 20
    },
    "conjuration": {
        "min_talents": 30
    }
}

def validate_sphere(json_path):
    slug = os.path.splitext(os.path.basename(json_path))[0]
    html_matches = glob.glob(os.path.join(RAW_DIR, "**", f"{slug}.html"), recursive=True)
    html_path = html_matches[0] if html_matches else None

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    issues = []
    warnings = []

    talents = data.get("talents", [])
    total_talents = len(talents)

    # 1. Validación básica de conteo
    if total_talents == 0:
        issues.append("CRÍTICO: No se extrajo ningún talento de la esfera.")
    elif total_talents < 5:
        warnings.append(f"ADVERTENCIA: Cantidad muy baja de talentos ({total_talents}).")

    # 2. Validación de campos de talentos
    seen_names = set()
    empty_desc_count = 0
    all_tags = set()

    for idx, t in enumerate(talents):
        name = t.get("name", "").strip()
        if not name:
            issues.append(f"Talento #{idx} tiene nombre vacío.")
        elif name in seen_names:
            warnings.append(f"Talento duplicado detectado: '{name}'.")
        seen_names.add(name)

        desc = t.get("description", "").strip()
        if not desc:
            empty_desc_count += 1

        for tag in t.get("tags", []):
            all_tags.add(tag.lower())

    if empty_desc_count > 0:
        warnings.append(f"{empty_desc_count} talentos tienen descripción vacía.")

    # 3. Validación de heurísticas específicas de esfera
    reqs = SPHERE_SPECIAL_REQUIREMENTS.get(slug.lower())
    if reqs:
        if "min_talents" in reqs and total_talents < reqs["min_talents"]:
            warnings.append(f"Se esperaban al menos {reqs['min_talents']} talentos para {slug} (encontrados: {total_talents}).")

        if "required_tags" in reqs:
            for req_tag in reqs["required_tags"]:
                # Verificar si alguna variante del tag está presente
                found = any(req_tag in t for t in all_tags)
                if not found:
                    issues.append(f"Falta categoría/tag requerida: '[{req_tag}]' no detectada en talentos.")

    # 4. Chequeo de encabezados huérfanos en HTML (si está disponible)
    if html_path and os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as hf:
            soup = BeautifulSoup(hf.read(), "html.parser")
            page_content = soup.find("div", id="page-content")
            if page_content:
                # Contar encabezados h4 totales en el HTML
                h4_count = len(page_content.find_all("h4"))
                if h4_count > total_talents + 5: # Margen para subtítulos generales
                    warnings.append(f"Posibles talentos huérfanos: HTML tiene {h4_count} encabezados <h4> pero solo se extrajeron {total_talents} talentos.")

    status = "FAILED" if issues else ("WARNING" if warnings else "PASSED")

    return {
        "slug": slug,
        "name": data.get("sphere_name", slug),
        "status": status,
        "total_talents": total_talents,
        "issues": issues,
        "warnings": warnings,
        "detected_tags": sorted(list(all_tags))
    }

def run_all_validations():
    json_files = glob.glob(os.path.join(JSON_DIR, "*.json"))
    if not json_files:
        print(f"⚠️ No se encontraron JSONs en {JSON_DIR}. Ejecuta primero 'parsers/parse_sphere.py'.")
        return

    print("==================================================")
    print("🔍 Auditoría de Integridad de Esferas (Capa 2)")
    print(f"📁 Directorio analizado: {JSON_DIR}")
    print(f"📊 Total de esferas a validar: {len(json_files)}")
    print("==================================================\n")

    results = []
    passed = 0
    with_warnings = 0
    failed = 0

    for jf in sorted(json_files):
        res = validate_sphere(jf)
        results.append(res)

        if res["status"] == "PASSED":
            passed += 1
            print(f"✅ [PASSED]  {res['name']:20} ({res['total_talents']:2} talentos | Tags: {len(res['detected_tags'])})")
        elif res["status"] == "WARNING":
            with_warnings += 1
            print(f"⚠️  [WARNING] {res['name']:20} ({res['total_talents']:2} talentos)")
            for w in res["warnings"]:
                print(f"    🔸 {w}")
        else:
            failed += 1
            print(f"❌ [FAILED]  {res['name']:20} ({res['total_talents']:2} talentos)")
            for err in res["issues"]:
                print(f"    🚫 {err}")
            for w in res["warnings"]:
                print(f"    🔸 {w}")

    print("\n==================================================")
    print("🏁 Resumen de Calidad")
    print(f"✅ Válidas al 100% : {passed}")
    print(f"⚠️  Con Advertencias : {with_warnings}")
    print(f"❌ Fallidas         : {failed}")
    print("==================================================")

    if failed > 0:
        print("\n💡 Recomendación: Asignar un subagente para crear parsers especializados en las esferas fallidas.")

if __name__ == "__main__":
    run_all_validations()
