from collections import defaultdict

from base import Entity, EntityType
from config.config import REMOVE_DEAD_ENTITIES_EVERY

class Game:
    def __init__(self) -> None:
        self.entities: defaultdict[EntityType, list[Entity]] = defaultdict(list)

    def update(self) -> None:
        pass

    def remove_dead_entities(self):
        """
        Remove all dead entities.
        This is called every REMOVE_DEAD_ENTITIES_EVERY game ticks
        """
        new_entities = defaultdict(list)
        for entity_type, entities in self.entities.items():
            for entity in entities:
                if entity.is_alive():
                    new_entities[entity_type].append(entity)
        self.entities = new_entities
