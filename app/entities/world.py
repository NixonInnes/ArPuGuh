import config
from app.database import session, models
from app.system.window import Window
from app.system.utils import Coord, distance


class World:

    def __init__(self):
        self.loaded_chunks = {}
        self.chunks_to_load = {}
        self.chunks_to_unload = []
        self.players = []


    def get_origin(self):
        origin = self.loaded_chunks.get(Coord(0,0))
        if not origin:
            origin = self.load_chunk(*Coord(0,0), create=True)
        return origin


    def get_window(self):
        player = self.init_player()
        window = Window(self, player)
        return window


    def init_player(self, name='player'):
        from app.entities.player import Player
        chunk = self.get_origin()
        player = Player(chunk=chunk,
                        x=config.window_width//2,
                        y=config.window_height//2,
                        width=50,
                        height=50,
                        name=name,
                        group=chunk.foreground)
        self.players.append(player)
        player.move_to_chunk(chunk)
        return player


    def load_chunk(self, x, y, create=False):
        from app.entities.chunk import Chunk
        chunk = self.loaded_chunks.get(Coord(x,y))
        if chunk is not None:
            return chunk
        chunk = Chunk.load(x, y, create)
        self.chunks_to_load[Coord(x, y)] = chunk
        return chunk
        

    def update(self, dt):
        chunks_to_unload = []
        for chunk in self.loaded_chunks.values():
            players_near_chunk = []
            for player in self.players:
                if distance(player.chunk.x, player.chunk.y,
                            chunk.x, chunk.y) > config.chunk_in_memory_distance:
                    players_near_chunk.append(False)
                else:
                    players_near_chunk.append(True)
            if not any(players_near_chunk):
                chunks_to_unload.append(chunk.coord)
            else:
                chunk.update()
        [self.loaded_chunks.pop(coord) for coord in chunks_to_unload]
        self.loaded_chunks.update(self.chunks_to_load)
        self.chunks_to_load.clear()