from collections import defaultdict

from base import Entity, EntityType
from config.back import REMOVE_DEAD_ENTITIES_EVERY
from utils import Timer

class Game:
    def __init__(self) -> None:
        self.entities: defaultdict[EntityType, list[Entity]] = defaultdict(list)
        self.remove_dead_entities_timer = Timer(max_time=REMOVE_DEAD_ENTITIES_EVERY)

    def update(self, time_delta: float) -> None:
        self.remove_dead_entities_timer.tick(time_delta)
        if not self.remove_dead_entities_timer.running():
            self.remove_dead_entities()

    def remove_dead_entities(self):
        """
        Remove all dead entities.
        This function is called every REMOVE_DEAD_ENTITIES_EVERY seconds.
        """
        new_entities = defaultdict(list)
        for entity_type, entities in self.entities.items():
            for entity in entities:
                if entity.is_alive():
                    new_entities[entity_type].append(entity)
        self.entities = new_entities
        self.remove_dead_entities_timer.reset()