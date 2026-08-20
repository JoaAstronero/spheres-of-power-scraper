#!/usr/bin/env python3
"""
Spheres of Power Wiki - Compilador Semántico de Fórmulas y Reglas (Capa 3)
--------------------------------------------------------------------------
Lee los JSONs de Capa 2 y enriquece cada talento con atributos evaluables:
- Economía de acciones (standard, swift, move, free, immediate)
- Costos de Spell Points
- Rangos computables (touch, close, medium, long)
- Fórmulas de daño y escalado (@cl, @bab, @str)
- Tiradas de salvación y fórmulas de CD (@casting_mod)
Guarda los resultados en data/json_layer3/spheres/.
"""

import glob
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYER2_SPHERES_DIR = os.path.join(BASE_DIR, "data", "json_layer2", "spheres")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "json_layer3", "spheres")

def compile_rule_semantics(text):
    """Extrae mecánicas, fórmulas y economía de acciones desde la prosa de la regla."""
    if not text:
        return {}

    semantics = {}

    # 1. Economía de Acciones
    if re.search(r"\bas a standard action\b", text, re.I):
        semantics["action_cost"] = "standard"
    elif re.search(r"\bas a swift action\b", text, re.I):
        semantics["action_cost"] = "swift"
    elif re.search(r"\bas a move action\b", text, re.I):
        semantics["action_cost"] = "move"
    elif re.search(r"\bas a full-round action\b", text, re.I):
        semantics["action_cost"] = "full_round"
    elif re.search(r"\bas a free action\b", text, re.I):
        semantics["action_cost"] = "free"
    elif re.search(r"\bas an immediate action\b", text, re.I):
        semantics["action_cost"] = "immediate"
    elif re.search(r"\bpassive\b|\bconstant bonus\b", text, re.I):
        semantics["action_cost"] = "passive"

    # 2. Costo de Spell Points
    sp_match = re.search(r"spend(?:ing)? (\d+) spell point", text, re.I)
    if sp_match:
        semantics["spell_point_cost"] = int(sp_match.group(1))
    elif re.search(r"costs? a spell point|spend a spell point", text, re.I):
        semantics["spell_point_cost"] = 1

    # 3. Rango
    if re.search(r"\bclose range\b|\bclose \(25", text, re.I):
        semantics["range"] = {"type": "close", "formula": "25 + floor(@cl / 2) * 5"}
    elif re.search(r"\bmedium range\b|\bmedium \(100", text, re.I):
        semantics["range"] = {"type": "medium", "formula": "100 + @cl * 10"}
    elif re.search(r"\blong range\b|\blong \(400", text, re.I):
        semantics["range"] = {"type": "long", "formula": "400 + @cl * 40"}
    elif re.search(r"\btouch range\b|\btouched creature\b", text, re.I):
        semantics["range"] = {"type": "touch"}

    # 4. Fórmulas de Daño y Escalado
    if re.search(r"1d6(?:\s*points of\s*\w*\s*damage)?\s*(?:plus|\+)\s*1d6 per (?:2|two) caster levels (?:beyond|above) 1st", text, re.I):
        semantics["damage_formula"] = "1d6 + floor((@cl - 1) / 2)d6"
    elif re.search(r"1d4\s*\+\s*1/2 (?:your )?caster level", text, re.I):
        semantics["scaling_formula"] = "1d4 + floor(@cl / 2)"
    elif re.search(r"(?:damage|healing|points) equal to (?:your )?caster level", text, re.I):
        semantics["scaling_formula"] = "@cl"
    elif re.search(r"1 (?:point|round|bonus)? per (?:2|two) caster levels", text, re.I):
        semantics["scaling_formula"] = "floor(@cl / 2)"
    elif re.search(r"1 (?:point|round|bonus)? per (?:4|four) caster levels", text, re.I):
        semantics["scaling_formula"] = "floor(@cl / 4)"
    elif re.search(r"1 (?:point|round|bonus)? per (?:5|five) caster levels", text, re.I):
        semantics["scaling_formula"] = "floor(@cl / 5)"

    # 5. Salvaciones y CD
    save_match = re.search(r"(Fortitude|Reflex|Will) save (?:to |for )?(negates|half|reduces|avoids)?", text, re.I)
    if save_match:
        semantics["saving_throw"] = {
            "type": save_match.group(1).lower(),
            "effect": save_match.group(2).lower() if save_match.group(2) else "negates",
            "dc_formula": "10 + floor(@cl / 2) + @casting_mod"
        }

    return semantics

def process_sphere_layer3(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    enriched_talents = []
    enriched_count = 0

    for t in data.get("talents", []):
        text_to_eval = t.get("description", "")
        # Si tiene sub-traits, concatenar texto para análisis semántico
        for st in t.get("sub_traits", []):
            text_to_eval += "\n" + st.get("effect", "")

        semantics = compile_rule_semantics(text_to_eval)
        if semantics:
            enriched_count += 1

        enriched_talents.append({
            **t,
            "mechanics": semantics
        })

    data["talents"] = enriched_talents
    data["layer3_enriched_talents_count"] = enriched_count

    return data

def run_layer3_compilation():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    json_files = glob.glob(os.path.join(LAYER2_SPHERES_DIR, "*.json"))

    if not json_files:
        print(f"⚠️ No se encontraron archivos JSON en {LAYER2_SPHERES_DIR}.")
        return

    print(f"🧠 Compilando {len(json_files)} esferas a Capa 3 (Semántica y Fórmulas)...")
    total_enriched = 0
    total_talents_all = 0

    for jf in sorted(json_files):
        enriched_data = process_sphere_layer3(jf)
        slug = os.path.splitext(os.path.basename(jf))[0]
        out_file = os.path.join(OUTPUT_DIR, f"{slug}.json")

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(enriched_data, f, indent=2, ensure_ascii=False)

        total_enriched += enriched_data["layer3_enriched_talents_count"]
        total_talents_all += enriched_data["total_talents"]
        print(f"  ✨ {enriched_data['sphere_name']:22} -> {enriched_data['layer3_enriched_talents_count']:3}/{enriched_data['total_talents']:3} talentos enriquecidos con fórmulas")

    print(f"\n🎉 ¡Compilación de Capa 3 completada con éxito!")
    print(f"   📊 Total talentos con fórmulas/economía extraídas: {total_enriched} de {total_talents_all}")
    print(f"   📁 Directorio de salida: {OUTPUT_DIR}")

if __name__ == "__main__":
    run_layer3_compilation()
