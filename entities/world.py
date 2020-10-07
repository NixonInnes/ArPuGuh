from database import session, models
from entities.chunk import Chunk

class World:
    def __init__(self):
        self.loaded_tiles = []

    def get_origin(self):
        chunk = Chunk.load(0,0, create=True)
        return chunk