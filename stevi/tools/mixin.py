"""Phase-4-Werkzeug: ein Mixin-Gerüst erzeugen.

Ein Mixin greift in bestehenden Minecraft-Code ein, ohne ihn zu kopieren. Dieses
Werkzeug erzeugt eine Mixin-Klasse mit Beispiel-``@Inject`` und trägt sie in die
``<mod_id>.mixins.json`` ein (Seite: gemeinsam oder client).

Hinweis: Welche Methode/welcher Ziel-Deskriptor passt, ist versions- und
Mappings-abhängig. Das Gerüst enthält ein lauffähiges HEAD-Inject-Beispiel auf
``tick()`` als Ausgangspunkt, das Stevi/der Nutzer an das echte Ziel anpasst.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from . import project as P


def _pascal(name: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", name)
    return "".join(p[:1].upper() + p[1:] for p in parts) or "ExampleMixin"


def add_mixin(tool_input: dict[str, Any], workspace: Path) -> str:
    project = P.find_project(workspace, tool_input["mod"].strip())
    if project is None:
        return f"Keine Mod '{tool_input['mod']}' im Workspace gefunden."

    meta = P.read_mod_meta(project)
    mod_id, package = meta["mod_id"], meta["package"]

    target = (tool_input.get("target_class") or "net.minecraft.client.MinecraftClient").strip()
    target_simple = target.rsplit(".", 1)[-1]
    side = (tool_input.get("side") or "client").strip().lower()
    is_client = side == "client"
    mixin_name = _pascal(tool_input.get("mixin_name") or f"{target_simple}Mixin")

    sub_pkg = "mixin.client" if is_client else "mixin"
    mixin_pkg = f"{package}.{sub_pkg}"
    mixin_path = P.java_file(project, mixin_pkg, mixin_name)
    if mixin_path.exists():
        return f"Mixin '{mixin_name}' existiert bereits unter {mixin_pkg}."

    P.write_file(mixin_path, _mixin_class(mixin_pkg, target, target_simple, mixin_name))

    # In <mod_id>.mixins.json eintragen.
    cfg_path = project / f"src/main/resources/{mod_id}.mixins.json"
    note = _register_mixin(cfg_path, sub_pkg, mixin_name, is_client)

    return (
        f"✅ Mixin '{mixin_name}' angelegt (Ziel: {target}, Seite: {side}).\n"
        f"   • Datei: src/main/java/{mixin_pkg.replace('.', '/')}/{mixin_name}.java\n"
        f"   • {note}\n"
        f"   Passe Ziel-Methode und @Inject-Stelle an dein echtes Ziel an. "
        f"Danach mit build_mod prüfen."
    )


def _mixin_class(mixin_pkg: str, target_fqcn: str, target_simple: str, name: str) -> str:
    return f"""\
package {mixin_pkg};

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import {target_fqcn};

/**
 * Von Stevi generiertes Mixin-Gerüst für {target_simple}.
 * Beispiel: am Anfang von tick() einklinken. Methode/Stelle ggf. anpassen.
 */
@Mixin({target_simple}.class)
public class {name} {{

    @Inject(method = "tick", at = @At("HEAD"))
    private void stevi$onTick(CallbackInfo ci) {{
        // Dein Code, der bei jedem tick() von {target_simple} läuft.
    }}
}}
"""


def _register_mixin(cfg_path: Path, sub_pkg: str, mixin_name: str, is_client: bool) -> str:
    if not cfg_path.is_file():
        return f"Konnte {cfg_path.name} nicht finden — Eintrag bitte manuell ergänzen."
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return f"{cfg_path.name} ist kein gültiges JSON — Eintrag bitte manuell ergänzen."

    # Eintrag relativ zum konfigurierten "package" (das ist <basis>.mixin).
    # Gemeinsame Mixins → "Name"; Client-Mixins → "client.Name".
    entry = f"client.{mixin_name}" if is_client else mixin_name
    key = "client" if is_client else "mixins"
    arr = cfg.setdefault(key, [])
    if entry not in arr:
        arr.append(entry)
        cfg[key] = sorted(arr)
    cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return f"in {cfg_path.name} unter \"{key}\" eingetragen ({entry})"
