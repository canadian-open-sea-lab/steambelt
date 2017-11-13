import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship, sessionmaker
from geoalchemy2 import Geometry

import config


engine = sqlalchemy.create_engine(config.DATABASE_CONNECTOR)
Session = sessionmaker()
Session.configure(bind=engine)
Base = declarative_base()


class Grid(Base):
    __tablename__ = 'grid'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    # ullat = Column(Float, nullable=False)
    # ullon = Column(Float, nullable=False)
    # lrlat = Column(Float, nullable=False)
    # lrlon = Column(Float, nullable=False)
    bounding_box = Column('geom', Geometry('POLYGON', srid=4326))
    cell_width = Column(Float, nullable=False)
    cell_height = Column(Float, nullable=False)


class GridCell(Base):
    __tablename__ = 'grid_cell'

    id = Column(Integer, primary_key=True)
    grid_id = Column(Integer, ForeignKey('grid.id'))
    # ullat = Column(Float, nullable=False)
    # ullon = Column(Float, nullable=False)
    # lrlat = Column(Float, nullable=False)
    # lrlon = Column(Float, nullable=False)
    bounding_box = Column('geom', Geometry('POLYGON', srid=4326))


class DecisionLayer(Base):
    __tablename__ = 'decision_layer'

    id = Column(Integer, primary_key=True)
    grid_id = Column(Integer, ForeignKey('grid.id'))
    creation_time = Column(DateTime, nullable=False)


class DecisionLayerCell(Base):
    __tablename__ = 'decision_layer_cell'

    id = Column(Integer, primary_key=True)
    decision_layer_id = Column(Integer, ForeignKey('decision_layer.id'))
    grid_cell_id = Column(Integer, ForeignKey('grid_cell.id'))
    depth = Column(Float)
    temperature = Column(Float)
    wind_speed = Column(Float)



def main():
    Base.metadata.create_all(engine)
    return


if __name__ == '__main__':
    main()