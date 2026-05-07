"""
Event Bus - Système de messagerie asynchrone basé sur Redis Pub/Sub
Permet la communication découplée entre les plugins et le core
"""
import json
import asyncio
from typing import Callable, Dict, Any, List, Optional
from datetime import datetime
import redis.asyncio as redis
from loguru import logger

from core.config import settings


class EventBus:
    """
    Event Bus pour la communication entre composants
    Utilise Redis Pub/Sub pour la messagerie asynchrone
    """
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.handlers: Dict[str, List[Callable]] = {}
        self.running: bool = False
        self._connection_pool: Optional[redis.ConnectionPool] = None
        
    async def connect(self) -> bool:
        """Établit la connexion à Redis"""
        try:
            self._connection_pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=settings.EVENT_BUS_CONNECT_TIMEOUT,
                socket_timeout=settings.EVENT_BUS_CONNECT_TIMEOUT,
                health_check_interval=30,
            )
            self.redis = redis.Redis(connection_pool=self._connection_pool)
            self.redis_client = self.redis
            
            # Test de connexion
            await self.redis.ping()
            logger.info("EventBus connected to Redis")
            return True
            
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory fallback: {e}")
            self.redis = None
            self.redis_client = None
            return False
    
    async def disconnect(self):
        """Ferme la connexion à Redis"""
        self.running = False
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
            self.redis_client = None
        if self._connection_pool:
            await self._connection_pool.disconnect()
        logger.info("EventBus disconnected")
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Souscrit à un type d'événement avec un handler
        Args:
            event_type: Type d'événement (ex: "prospect.created")
            handler: Fonction callback appelée quand l'événement est reçu
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.debug(f"Subscribed to {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Désouscrit un handler d'un type d'événement"""
        if event_type in self.handlers:
            self.handlers[event_type].remove(handler)
            if not self.handlers[event_type]:
                del self.handlers[event_type]
    
    async def publish(self, event_type: str, payload: Dict[str, Any], version: str = "1.0") -> bool:
        """
        Publie un événement sur le bus
        Args:
            event_type: Type d'événement (ex: "prospect.created")
            payload: Données de l'événement
            version: Version du format d'événement
        Returns:
            bool: True si publié avec succès
        """
        event = self._format_event(event_type, payload, version)
        event_json = json.dumps(event)
        
        try:
            if self.redis:
                # Publication via Redis
                await self.redis.publish(settings.EVENT_BUS_CHANNEL, event_json)
                logger.debug(f"Published event {event_type} to Redis")
            else:
                # Fallback in-memory: appel direct des handlers
                await self._dispatch_event(event)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            return False
    

    def _format_event(self, event_type: str, payload: Dict[str, Any], version: str = "1.0") -> Dict[str, Any]:
        """Formate un événement avec les métadonnées communes."""
        return {
            "type": event_type,
            "payload": payload,
            "version": version,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "b2b-prospector",
        }

    async def _dispatch_event(self, event: Dict[str, Any]) -> None:
        """Dispatch un événement aux handlers locaux"""
        event_type = event.get("type", "")
        
        # Handlers spécifiques au type
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"Handler error for {event_type}: {e}")
        
        # Handlers wildcard (*)
        if "*" in self.handlers:
            for handler in self.handlers["*"]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"Wildcard handler error for {event_type}: {e}")
    
    async def listen(self) -> None:
        """
        Écoute les événements en continu (mode subscriber)
        Doit être lancé dans une tâche asyncio
        """
        if not self.redis:
            logger.info("EventBus listening in in-memory mode")
            self.running = True
            while self.running:
                await asyncio.sleep(0.1)
            return
        
        try:
            self.pubsub = self.redis.pubsub()
            
            # S'abonner à tous les événements
            await self.pubsub.subscribe(settings.EVENT_BUS_CHANNEL)
            
            logger.info("EventBus listening to Redis events")
            self.running = True
            
            while self.running:
                try:
                    message = await self.pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0
                    )
                    
                    if message and message["type"] == "message":
                        data = json.loads(message["data"])
                        await self._dispatch_event(data)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in event listener: {e}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Failed to start event listener: {e}")
            raise
        finally:
            if self.pubsub:
                await self.pubsub.unsubscribe()
    
    async def emit(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """Alias pour publish"""
        return await self.publish(event_type, payload)


# Instance globale de l'EventBus
event_bus = EventBus()


async def get_event_bus() -> EventBus:
    """Retourne l'instance de l'EventBus"""
    if not event_bus.redis:
        await event_bus.connect()
    return event_bus
