# 📋 Bitácora de Errores y Backlog de Datos (Data Compilation Issues)

Este documento registra inconsistencias, errores de parseo, campos faltantes y casos borde detectados en los JSONs mientras desarrollamos el **Character Manager de PF1e + Spheres of Power**.

---

## 🚦 Leyenda de Estados
* 🔴 **CRÍTICO:** Bloquea el cálculo de reglas o cálculos del personaje.
* 🟡 **ADVERTENCIA:** Falta información opcional o el texto tiene formato desprolijo.
* 🟢 **RESUELTO:** El scraper/parser fue corregido y la base de datos fue actualizada.

---

## 🐛 Registro de Incidencias y Mejoras

| ID | Entidad / Archivo | Severidad | Descripción del Problema | Estado | Solución / Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-001** | `spheres/pilot.json` | 🟡 ADVERTENCIA | Esfera con 0 talentos extraídos en Capa 2. | 📝 Pendiente | La esfera está descontinuada en la wiki oficial de SoP. Evaluar si se excluye o se incluye texto de archivo. |
| **ISSUE-002** | `parsers/parse_sphere.py` | 🟡 ADVERTENCIA | 46 esferas tienen advertencias de "encabezados <h4> duplicados" en `validator.py`. | 📝 Pendiente | En la wiki, la pestaña "Original" y las tablas de contenido duplican los `<h4>`. El parser usa la pestaña "Ultimate" correctamente, pero el validador cuenta los `<h4>` del documento completo. |
| **ISSUE-003** | `parsers/compiler_layer3.py` | 🟡 ADVERTENCIA | 2.057 de 5.052 talentos tienen fórmulas automáticas; los restantes son talentos de utilidad/prosa compleja. | 📝 Pendiente | Pasar agentes de Antigravity CLI en lotes para enriquecer talentos de utilidad con tags semánticos avanzados. |

---

## 📝 Plantilla para Reportar Nuevos Errores durante el desarrollo del Character Manager

Cuando encuentres un error al construir la hoja de personaje, regístralo aquí con este formato:

```markdown
### [ISSUE-XXX] Nombre de la Esfera / Clase / Dote
* **Origen:** `data/json_layer3/spheres/alteration.json` (por ejemplo)
* **Comportamiento observado:** Falta el costo de Spell Points en el talento 'X' o la fórmula de daño no calculó el multiplicador de tamaño.
* **Comportamiento esperado:** `spell_point_cost: 1`, `damage_formula: "2d6 + @str"`.
* **Causa raíz:** Selector CSS o regex en `compiler_layer3.py`.
* **Acción requerida:** Actualizar parser y recompilar JSON.
```

---

## 🎯 Backlog de Expansión de Datos

- [ ] **Dotes Generales de PF1e:** Importar compendio base de dotes estándar (Power Attack, Weapon Focus, etc.).
- [ ] **Razas Base de PF1e:** Incorporar modificadores raciales estándar (`+2 Dex, -2 Con`, etc.).
- [ ] **Tablas de Equipo Base:** Cargar catálogo de armas, armaduras y escudos estándar con sus estadísticas (peso, precio, daño, crítico, CA).
