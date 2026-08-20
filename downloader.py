#!/usr/bin/env python3
"""
Spheres of Power Wiki - Downloader Resiliente (Capa 1)
------------------------------------------------------
Descarga y almacena en caché local las páginas HTML del manifest.json
con rate-limiting respetuoso, reintentos automáticos y soporte para pausar/reanudar.

Uso:
  python3 downloader.py                   # Descarga todo el manifest
  python3 downloader.py --category spheres # Descarga solo esferas
  python3 downloader.py --limit 10         # Descarga de prueba (primeras 10)
  python3 downloader.py --delay 1.5        # Ajustar delay entre peticiones
"""

import argparse
import json
import os
import sys
import time
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST_FILE = os.path.join(BASE_DIR, "manifest.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "raw_html")

USER_AGENT = "SpheresDataPipeline/1.0 (Educational/TTRPG Tool; Rate-Limited 1.2s)"

def load_manifest():
    if not os.path.exists(MANIFEST_FILE):
        print(f"❌ Error: No se encontró {MANIFEST_FILE}. Ejecuta primero 'python3 generate_manifest.py'")
        sys.exit(1)
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_download_tasks(manifest, target_category="all"):
    """Aplana el manifest en una lista de tareas estructuradas (categoría, nombre, slug, url)."""
    tasks = []

    def add_list(category_path, item_list):
        for item in item_list:
            if isinstance(item, dict) and "url" in item and "slug" in item:
                tasks.append({
                    "category": category_path,
                    "name": item.get("name", item["slug"]),
                    "slug": item["slug"],
                    "url": item["url"]
                })

    # Esferas
    if target_category in ["all", "spheres", "magic_spheres"]:
        add_list("spheres/magic", manifest.get("spheres", {}).get("magic", []))
    if target_category in ["all", "spheres", "combat_spheres"]:
        add_list("spheres/combat", manifest.get("spheres", {}).get("combat", []))
    if target_category in ["all", "spheres", "skill_spheres"]:
        add_list("spheres/skill", manifest.get("spheres", {}).get("skill", []))

    # Clases
    if target_category in ["all", "classes"]:
        for subcat, classes in manifest.get("classes", {}).items():
            add_list(f"classes/{subcat}", classes)

    # Opciones y Reglas
    if target_category in ["all", "rules", "options"]:
        for subcat, options in manifest.get("options_and_rules", {}).items():
            add_list(f"options/{subcat}", options)

    # Equipo y Objetos
    if target_category in ["all", "gear", "items"]:
        for subcat, items in manifest.get("gear_and_items", {}).items():
            add_list(f"gear/{subcat}", items)

    # Arquetipos
    if target_category in ["all", "archetypes"]:
        for base_class, arch_list in manifest.get("archetypes_by_class", {}).items():
            safe_class_name = base_class.lower().replace(" ", "_").replace(",", "")
            add_list(f"archetypes/{safe_class_name}", arch_list)

    # Eliminar duplicados manteniendo orden
    seen_urls = set()
    unique_tasks = []
    for t in tasks:
        if t["url"] not in seen_urls:
            seen_urls.add(t["url"])
            unique_tasks.append(t)

    return unique_tasks

def download_page(session, url, destination_path, max_retries=3):
    """Descarga una página con reintentos exponenciales en caso de fallos de red."""
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code == 200:
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                with open(destination_path, "w", encoding="utf-8") as f:
                    f.write(resp.text)
                return True, len(resp.content), None
            elif resp.status_code == 429 or resp.status_code == 503:
                wait_time = attempt * 3
                time.sleep(wait_time)
            else:
                return False, 0, f"HTTP {resp.status_code}"
        except requests.exceptions.RequestException as e:
            if attempt == max_retries:
                return False, 0, str(e)
            time.sleep(attempt * 2)
    return False, 0, "Max retries exceeded"

def run_downloader(category="all", delay=1.2, limit=None, force=False):
    manifest = load_manifest()
    tasks = extract_download_tasks(manifest, category)

    if limit and limit > 0:
        tasks = tasks[:limit]

    total_tasks = len(tasks)
    print("==================================================")
    print("🚀 Spheres of Power - Downloader de Capa 1")
    print(f"📦 Total de páginas en cola : {total_tasks}")
    print(f"⏱️  Delay entre peticiones   : {delay:.2f}s")
    print(f"📁 Directorio de destino    : {OUTPUT_DIR}")
    print(f"🎯 Categoría seleccionada   : {category}")
    print("==================================================\n")

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    downloaded = 0
    skipped = 0
    failed = 0
    total_bytes = 0

    start_time = time.time()

    try:
        for idx, task in enumerate(tasks, 1):
            dest_file = os.path.join(OUTPUT_DIR, task["category"], f"{task['slug']}.html")
            
            # Si ya existe y no forzamos, omitir
            if os.path.exists(dest_file) and not force:
                file_size = os.path.getsize(dest_file)
                total_bytes += file_size
                skipped += 1
                print(f"[{idx}/{total_tasks}] ⏩ OMITIDA (Ya existe): [{task['category']}] {task['name']} ({file_size / 1024:.1f} KB)")
                continue

            # Descargar
            success, bytes_count, err_msg = download_page(session, task["url"], dest_file)

            if success:
                downloaded += 1
                total_bytes += bytes_count
                print(f"[{idx}/{total_tasks}] ✅ OK ({bytes_count / 1024:.1f} KB): [{task['category']}] {task['name']}")
            else:
                failed += 1
                print(f"[{idx}/{total_tasks}] ❌ ERROR ({err_msg}): [{task['category']}] {task['name']} ({task['url']})")

            # Delay respetuoso
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\n\n⚠️ Descarga pausada por el usuario (Ctrl+C). Puedes reanudar cuando quieras.")

    elapsed = time.time() - start_time
    print("\n==================================================")
    print("🏁 Resumen de Descarga")
    print(f"⏱️  Tiempo transcurrido : {elapsed:.1f} segundos")
    print(f"📥 Descargadas nuevas   : {downloaded}")
    print(f"⏩ Omitidas (en caché) : {skipped}")
    print(f"❌ Fallidas             : {failed}")
    print(f"💾 Espacio en disco     : {total_bytes / (1024 * 1024):.2f} MB")
    print("==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Downloader con caché para Spheres of Power")
    parser.add_argument("--category", default="all", help="Categoría a descargar (all, spheres, classes, archetypes, rules, gear)")
    parser.add_argument("--delay", type=float, default=1.2, help="Delay en segundos entre peticiones (default: 1.2)")
    parser.add_argument("--limit", type=int, default=None, help="Límite de páginas para prueba rápida")
    parser.add_argument("--force", action="store_true", help="Sobrescribir archivos existentes")

    args = parser.parse_args()
    run_downloader(category=args.category, delay=args.delay, limit=args.limit, force=args.force)
