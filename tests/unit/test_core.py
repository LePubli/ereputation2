"""
Tests unitaires pour le Core - Config, Event Bus, Plugin Manager
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

# Tests pour core/config.py
class TestConfig:
    """Tests de la configuration"""
    
    def test_settings_default_values(self):
        """Test des valeurs par défaut des settings"""
        from core.config import settings
        
        assert settings.APP_NAME == "B2B Prospector"
        assert settings.DEBUG is True
        assert settings.API_PORT == 8000
        assert settings.REDIS_HOST == "localhost"
    
    def test_settings_from_env(self):
        """Test de chargement depuis les variables d'environnement"""
        import os
        os.environ["DEBUG"] = "false"
        os.environ["API_PORT"] = "9000"
        
        # Recharger les settings (dans un vrai test, on utiliserait un fixture)
        from pydantic_settings import BaseSettings
        from core.config import Settings
        
        settings = Settings()
        assert settings.DEBUG is False
        assert settings.API_PORT == 9000
        
        # Cleanup
        del os.environ["DEBUG"]
        del os.environ["API_PORT"]


# Tests pour core/event_bus.py
class TestEventBus:
    """Tests de l'Event Bus Redis"""
    
    @pytest.mark.asyncio
    async def test_event_bus_connect(self):
        """Test de connexion à Redis"""
        from core.event_bus import EventBus
        
        event_bus = EventBus()
        
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_redis.return_value.ping = AsyncMock(return_value=True)
            await event_bus.connect()
            
            assert event_bus.redis_client is not None
            mock_redis.return_value.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_event_bus_publish(self):
        """Test de publication d'événement"""
        from core.event_bus import EventBus
        
        event_bus = EventBus()
        event_bus.redis_client = AsyncMock()
        event_bus.redis_client.publish = AsyncMock(return_value=1)
        
        payload = {"prospect_id": 123, "siren": "123456789"}
        await event_bus.publish("prospect.created", payload)
        
        event_bus.redis_client.publish.assert_called_once()
        call_args = event_bus.redis_client.publish.call_args
        assert call_args[0][0] == "prospector.events"
    
    @pytest.mark.asyncio
    async def test_event_bus_subscribe(self):
        """Test d'abonnement à un événement"""
        from core.event_bus import EventBus
        
        event_bus = EventBus()
        handler = AsyncMock()
        
        event_bus.subscribe("prospect.created", handler)
        
        assert "prospect.created" in event_bus.handlers
        assert handler in event_bus.handlers["prospect.created"]
    
    @pytest.mark.asyncio
    async def test_event_format(self):
        """Test du format des événements"""
        from core.event_bus import EventBus
        
        event_bus = EventBus()
        payload = {"test": "data"}
        
        event = event_bus._format_event("test.event", payload)
        
        assert event["type"] == "test.event"
        assert event["payload"] == payload
        assert event["version"] == "1.0"
        assert "timestamp" in event


# Tests pour core/plugin_manager.py
class TestPluginManager:
    """Tests du Plugin Manager"""
    
    def test_plugin_discovery(self):
        """Test de découverte des plugins"""
        from core.plugin_manager import PluginManager
        
        pm = PluginManager()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.iterdir', return_value=[
                MagicMock(name="scraper-insee"),
                MagicMock(name="audit-digital"),
            ]):
                with patch('yaml.safe_load', return_value={
                    "name": "test-plugin",
                    "version": "1.0.0",
                    "active": True
                }):
                    plugins = pm.discover()
                    
                    assert isinstance(plugins, list)
    
    def test_plugin_load(self):
        """Test de chargement d'un plugin"""
        from core.plugin_manager import PluginManager, PluginInfo
        
        pm = PluginManager()
        
        plugin_info = PluginInfo(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            active=True,
            dependencies=[],
            events_published=[],
            events_subscribed=[],
            endpoints=[]
        )
        
        pm.plugins["test-plugin"] = plugin_info
        
        result = pm.enable("test-plugin")
        assert result is True
        assert pm.get_active() == ["test-plugin"]
    
    def test_plugin_dependencies(self):
        """Test de vérification des dépendances"""
        from core.plugin_manager import PluginManager, PluginInfo
        
        pm = PluginManager()
        
        # Plugin avec dépendance
        plugin_a = PluginInfo(
            name="plugin-a",
            version="1.0.0",
            description="Plugin A",
            active=False,
            dependencies=["plugin-b"],
            events_published=[],
            events_subscribed=[],
            endpoints=[]
        )
        
        pm.plugins["plugin-a"] = plugin_a
        
        # Dépendance non satisfaite
        can_load = pm._check_dependencies("plugin-a")
        assert can_load is False
        
        # Ajouter la dépendance
        plugin_b = PluginInfo(
            name="plugin-b",
            version="1.0.0",
            description="Plugin B",
            active=True,
            dependencies=[],
            events_published=[],
            events_subscribed=[],
            endpoints=[]
        )
        pm.plugins["plugin-b"] = plugin_b
        
        can_load = pm._check_dependencies("plugin-a")
        assert can_load is True
    
    def test_get_all_endpoints(self):
        """Test de récupération de tous les endpoints"""
        from core.plugin_manager import PluginManager, PluginInfo
        
        pm = PluginManager()
        
        plugin_info = PluginInfo(
            name="test-plugin",
            version="1.0.0",
            description="Test",
            active=True,
            dependencies=[],
            events_published=[],
            events_subscribed=[],
            endpoints=[
                {"path": "/api/v1/test", "method": "GET"},
                {"path": "/api/v1/test", "method": "POST"}
            ]
        )
        
        pm.plugins["test-plugin"] = plugin_info
        
        endpoints = pm.get_all_endpoints()
        
        assert len(endpoints) == 2
        assert any(e["path"] == "/api/v1/test" and e["method"] == "GET" for e in endpoints)


# Tests d'intégration pour le cycle de vie
class TestApplicationLifecycle:
    """Tests du cycle de vie de l'application"""
    
    @pytest.mark.asyncio
    async def test_lifespan_startup(self):
        """Test du démarrage de l'application"""
        from main import lifespan
        from fastapi import FastAPI
        
        app = FastAPI()
        
        # Mock event_bus et plugin_manager
        with patch('main.event_bus') as mock_event_bus:
            with patch('main.plugin_manager') as mock_plugin_manager:
                mock_event_bus.connect = AsyncMock()
                mock_event_bus.listen = AsyncMock()
                mock_event_bus.disconnect = AsyncMock()
                
                mock_plugin_manager.discover = MagicMock(return_value=["plugin1"])
                mock_plugin_manager.initialize_all = MagicMock(return_value=1)
                mock_plugin_manager.get_active = MagicMock(return_value=["plugin1"])
                
                async with lifespan(app):
                    # Startup s'est bien passé
                    mock_event_bus.connect.assert_called_once()
                    mock_plugin_manager.discover.assert_called_once()
                    mock_plugin_manager.initialize_all.assert_called_once()
                
                # Shutdown s'est bien passé
                mock_event_bus.disconnect.assert_called_once()


# Run tests with: pytest tests/unit/test_core.py -v
