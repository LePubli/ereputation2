"""
Plugin Manager - Système de découverte et chargement des plugins
Scan le répertoire /plugins, charge les manifest.yaml et gère le cycle de vie
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from loguru import logger

from core.config import settings


@dataclass
class PluginInfo:
    """Informations sur un plugin"""
    name: str
    version: str
    description: str
    author: str = ""
    active: bool = False
    dependencies: List[str] = field(default_factory=list)
    endpoints: List[Dict[str, Any]] = field(default_factory=list)
    events_published: List[str] = field(default_factory=list)
    events_subscribed: List[str] = field(default_factory=list)
    path: Optional[Path] = None
    manifest: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_manifest(cls, manifest: Dict[str, Any], path: Path) -> "PluginInfo":
        """Crée une PluginInfo depuis un manifest.yaml"""
        return cls(
            name=manifest.get("name", "unknown"),
            version=manifest.get("version", "0.0.0"),
            description=manifest.get("description", ""),
            author=manifest.get("author", ""),
            active=manifest.get("active", False),
            dependencies=manifest.get("dependencies", []),
            endpoints=manifest.get("endpoints", []),
            events_published=manifest.get("events_published", []),
            events_subscribed=manifest.get("events_subscribed", []),
            path=path,
            manifest=manifest
        )


class PluginManager:
    """
    Gestionnaire de plugins
    Découvre, charge et gère le cycle de vie des plugins
    """
    
    def __init__(self):
        self.plugins: Dict[str, PluginInfo] = {}
        self.loaded_modules: Dict[str, Any] = {}
        self.plugins_dir = Path(settings.PLUGINS_DIR)
        
    def discover(self) -> List[str]:
        """
        Scanne le répertoire des plugins et découvre les plugins disponibles
        Returns:
            Liste des noms de plugins découverts
        """
        discovered = []
        
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory does not exist: {self.plugins_dir}")
            return discovered
        
        # Scan chaque sous-répertoire
        for item in self.plugins_dir.iterdir():
            if not item.is_dir():
                continue
            
            # Vérifie la présence de manifest.yaml
            manifest_path = item / "manifest.yaml"
            if not manifest_path.exists():
                logger.debug(f"No manifest.yaml in {item.name}, skipping")
                continue
            
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = yaml.safe_load(f)
                
                plugin_info = PluginInfo.from_manifest(manifest, item)
                self.plugins[plugin_info.name] = plugin_info
                discovered.append(plugin_info.name)
                
                logger.info(f"Discovered plugin: {plugin_info.name} v{plugin_info.version}")
                
            except Exception as e:
                logger.error(f"Failed to load manifest from {item.name}: {e}")
        
        logger.info(f"Discovered {len(discovered)} plugins")
        return discovered
    
    def validate_dependencies(self, plugin_name: str) -> bool:
        """
        Vérifie que toutes les dépendances d'un plugin sont satisfaites
        Args:
            plugin_name: Nom du plugin à valider
        Returns:
            True si toutes les dépendances sont satisfaites
        """
        if plugin_name not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_name]
        
        for dep in plugin.dependencies:
            # Vérifie si la dépendance est un autre plugin
            if dep in self.plugins:
                if not self.plugins[dep].active:
                    logger.warning(f"Plugin {plugin_name} requires inactive plugin {dep}")
                    return False
            else:
                # Dépendance externe (à implémenter selon les besoins)
                logger.debug(f"External dependency {dep} for {plugin_name}")
        
        return True
    
    def _check_dependencies(self, plugin_name: str) -> bool:
        """Alias rétrocompatible pour validate_dependencies."""
        return self.validate_dependencies(plugin_name)

    def load(self, plugin_name: str) -> bool:
        """
        Charge un plugin spécifique
        Args:
            plugin_name: Nom du plugin à charger
        Returns:
            True si chargé avec succès
        """
        if plugin_name not in self.plugins:
            logger.error(f"Plugin {plugin_name} not found")
            return False
        
        plugin = self.plugins[plugin_name]
        
        # Vérifie les dépendances
        if not self.validate_dependencies(plugin_name):
            logger.error(f"Dependencies not satisfied for {plugin_name}")
            return False
        
        # Cherche le module principal du plugin
        main_module = None
        possible_files = ["main.py", "plugin.py", f"{plugin_name.replace('-', '_')}.py"]
        
        for filename in possible_files:
            module_path = plugin.path / filename
            if module_path.exists():
                main_module = module_path
                break
        
        if not main_module:
            logger.warning(f"No main module found for {plugin_name}")
            # Plugin sans code Python (seulement manifest)
            plugin.active = True
            return True
        
        try:
            # Import dynamique du module
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_name}",
                main_module
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.loaded_modules[plugin_name] = module
                
                # Appelle la fonction d'initialisation si elle existe
                if hasattr(module, 'init'):
                    module.init()
                
                plugin.active = True
                logger.info(f"Loaded plugin: {plugin_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return False
    
    def unload(self, plugin_name: str) -> bool:
        """
        Décharge un plugin
        Args:
            plugin_name: Nom du plugin à décharger
        Returns:
            True si déchargé avec succès
        """
        if plugin_name not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_name]
        
        # Appelle la fonction de cleanup si elle existe
        if plugin_name in self.loaded_modules:
            module = self.loaded_modules[plugin_name]
            if hasattr(module, 'cleanup'):
                try:
                    module.cleanup()
                except Exception as e:
                    logger.error(f"Error during cleanup of {plugin_name}: {e}")
            
            del self.loaded_modules[plugin_name]
        
        plugin.active = False
        logger.info(f"Unloaded plugin: {plugin_name}")
        return True
    
    def get_active(self) -> List[str]:
        """Retourne la liste des plugins actifs"""
        return [name for name, plugin in self.plugins.items() if plugin.active]
    
    def get_inactive(self) -> List[str]:
        """Retourne la liste des plugins inactifs"""
        return [name for name, plugin in self.plugins.items() if not plugin.active]
    
    def enable(self, plugin_name: str) -> bool:
        """Active un plugin"""
        if self.load(plugin_name):
            logger.info(f"Enabled plugin: {plugin_name}")
            return True
        return False
    
    def disable(self, plugin_name: str) -> bool:
        """Désactive un plugin"""
        if self.unload(plugin_name):
            logger.info(f"Disabled plugin: {plugin_name}")
            return True
        return False
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInfo]:
        """Retourne les informations d'un plugin"""
        return self.plugins.get(plugin_name)
    
    def get_all_endpoints(self) -> List[Dict[str, Any]]:
        """Retourne tous les endpoints de tous les plugins"""
        endpoints = []
        for plugin in self.plugins.values():
            for endpoint in plugin.endpoints:
                endpoint["plugin"] = plugin.name
                endpoints.append(endpoint)
        return endpoints
    
    def initialize_all(self) -> int:
        """
        Initialise tous les plugins marqués comme actifs dans la config
        Returns:
            Nombre de plugins initialisés avec succès
        """
        loaded_count = 0
        
        active_plugins = settings.active_plugins_list
        if not active_plugins:
            active_plugins = [
                name for name, plugin in self.plugins.items() if plugin.active
            ]

        for plugin_name in active_plugins:
            if plugin_name in self.plugins:
                if self.enable(plugin_name):
                    loaded_count += 1
            else:
                logger.warning(f"Plugin {plugin_name} in ACTIVE_PLUGINS but not discovered")
        
        logger.info(f"Initialized {loaded_count}/{len(active_plugins)} configured plugins")
        return loaded_count


# Instance globale du PluginManager
plugin_manager = PluginManager()


def get_plugin_manager() -> PluginManager:
    """Retourne l'instance du PluginManager"""
    return plugin_manager
