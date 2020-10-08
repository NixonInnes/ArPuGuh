from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

from app.system.utils import Coord


engine = create_engine('sqlite:///db.sqlite')
Base = declarative_base()


class Block(Base):
    __tablename__ = 'blocks'
    id = Column(Integer, primary_key=True)
    x = Column(Integer, index=True)
    y = Column(Integer, index=True)

    z = Column(Integer)
    foliage = Column(Integer)

    chunk_id = Column(Integer, ForeignKey('chunks.id'))

    def __repr__(self):
      return '<Block id: %s, chunk: %s, coord: (%s,%s)>' % (self.id, 
                                                            self.chunk.id if self.chunk else '-',
                                                            self.x, 
                                                            self.y)


class Chunk(Base):
    __tablename__ = 'chunks'
    id = Column(Integer, primary_key=True)
    x = Column(Integer, index=True)
    y = Column(Integer, index=True)
    name = Column(String)
    temperature = Column(Float)
    precipitation = Column(Float)
    windspeed = Column(Float)

    blocks = relationship('Block', backref='tile')

    n_id = Column(Integer, ForeignKey('chunks.id'))
    n = relationship('Chunk', 
                     foreign_keys=[n_id], 
                     uselist=False, 
                     backref=backref('s', uselist=False, remote_side=[id]))

    ne_id = Column(Integer, ForeignKey('chunks.id'))
    ne = relationship('Chunk', 
                      foreign_keys=[ne_id], 
                      uselist=False, 
                      backref=backref('sw', uselist=False, remote_side=[id]))

    e_id = Column(Integer, ForeignKey('chunks.id'))
    e = relationship('Chunk', 
                     foreign_keys=[e_id], 
                     uselist=False, 
                     backref=backref('w', uselist=False, remote_side=[id]))

    se_id = Column(Integer, ForeignKey('chunks.id'))
    se = relationship('Chunk', 
                      foreign_keys=[se_id], 
                      uselist=False, 
                      backref=backref('nw', uselist=False, remote_side=[id]))

    @property
    def coord(self):
        return Coord(self.x, self.y)

    @property
    def adjacents(self):
        return {'nw': self.nw,
                'n': self.n,
                'ne': self.ne,
                'e': self.e,
                'se': self.se,
                's': self.s,
                'sw': self.sw,
                'w': self.w}

    def __repr__(self):
        return '<Chunk id: %s, coord: (%s,%s)>' % (self.id, self.x, self.y)


Base.metadata.create_all(engine)