"""
Plugin Registry — In-memory hot-reload system.
Tous les plugins sont chargés au démarrage.
Toggle = mise à jour DB + cache in-memory.
Aucun restart nécessaire.
"""
import importlib.util
import sys
from pathlib import Path
from typing import Any
from loguru import logger


class PluginRegistry:
    """Singleton registry — état in-memory de tous les plugins."""

    _instance: "PluginRegistry | None" = None

    def __new__(cls) -> "PluginRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._active: set[str] = set()
            cls._instance._manifests: dict[str, dict] = {}
            cls._instance._routers: dict[str, Any] = {}
        return cls._instance

    # ── État actif ──────────────────────────────────────────────
    def activate(self, name: str) -> None:
        self._active.add(name)

    def deactivate(self, name: str) -> None:
        self._active.discard(name)

    def is_active(self, name: str) -> bool:
        return name in self._active

    @property
    def active_plugins(self) -> set[str]:
        return set(self._active)

    # ── Manifests ───────────────────────────────────────────────
    def register_manifest(self, name: str, manifest: dict) -> None:
        self._manifests[name] = manifest

    def get_manifest(self, name: str) -> dict:
        return self._manifests.get(name, {})

    def all_manifests(self) -> dict[str, dict]:
        return dict(self._manifests)

    # ── Routers ─────────────────────────────────────────────────
    def register_router(self, name: str, router: Any) -> None:
        self._routers[name] = router

    def get_router(self, name: str) -> Any | None:
        return self._routers.get(name)


# Singleton global
registry = PluginRegistry()


def load_manifest(plugin_folder: str) -> dict:
    """Charge le manifest.yaml d'un plugin."""
    import yaml
    manifest_path = Path(f"plugins/{plugin_folder}/manifest.yaml")
    if manifest_path.exists():
        try:
            with open(manifest_path) as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.debug(f"[Registry] manifest {plugin_folder}: {e}")
    return {
        "name": plugin_folder,
        "version": "1.0.0",
        "description": f"Plugin {plugin_folder}",
        "author": "B2B Prospector",
        "category": "tools",
        "icon": "🔌",
        "is_core": False,
    }


def load_plugin_module(folder_name: str):
    """Charge dynamiquement un module plugin (supporte les tirets)."""
    module_name = folder_name.replace("-", "_")

    # Essaie d'abord l'import normal
    try:
        module = __import__(f"plugins.{module_name}", fromlist=["router"])
        return module
    except ImportError:
        pass

    # Fallback pour dossiers avec tirets
    for filename in ("__init__.py", "routes.py"):
        plugin_path = Path(f"plugins/{folder_name}/{filename}")
        if plugin_path.exists():
            try:
                spec = importlib.util.spec_from_file_location(
                    f"plugins_{module_name}", str(plugin_path)
                )
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[f"plugins_{module_name}"] = mod
                    spec.loader.exec_module(mod)
                    return mod
            except Exception as e:
                logger.debug(f"[Registry] load {folder_name}: {e}")
                break

    return None
