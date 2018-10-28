import sqlalchemy
import logging

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, Integer, String, Float, Table, Text, ForeignKey, \
create_engine, desc
from actions import Settings


model_logger = logging.getLogger('my_logger.model')
formatter_model = logging.Formatter('%(asctime)s - %(name)s - %(threadName)s - %(levelname)s - %(message)s')
Base = declarative_base()

class WeatherAll(Base):
    __tablename__ = 'weather_all'
    id = Column(Integer, primary_key=True)
    name = Column(String, ForeignKey('location.name'))
    dt = Column(Integer)
    base = Column(String)
    wind_speed = Column(Integer)
    wind_deg = Column(Integer)
    clouds_all = Column(Integer)
    rain_3h = Column(Float)
    snow_3h = Column(Float)
    main_temp = Column(Float)
    main_pressure = Column(Integer)
    main_humidity = Column(Integer)
    main_temp_min = Column(Float)
    main_temp_max = Column(Float)
    main_sea_level = Column(Float)
    main_grnd_level = Column(Float)

    def __repr__(self):
         return "<weather_all(name='%s', dt='%d')>" % (
                                  self.name, self.dt)

class Location(Base):
    __tablename__ = 'location'
    lon = Column(Float)
    lat = Column(Float)
    name = Column(String, primary_key=True)
    city_id = Column(Integer)
    weathers_all = relationship('WeatherAll', order_by=WeatherAll.id,
                                back_populates='location')

weather_types = Table('weather_types', Base.metadata,
                      Column('weather_all_id', ForeignKey('weather_all.id'),
                             primary_key=True),
                      Column('weather_id', ForeignKey('weather.id'),
                             primary_key=True))

class Weather(Base):
    __tablename__ = 'weather'
    id = Column(Integer, primary_key=True)
    main = Column(String)
    description = Column(String)
    icon = Column(String)
    weathers = relationship('WeatherAll',
                            secondary=weather_types,
                            back_populates='weathers')

WeatherAll.location = relationship('Location',
                                    back_populates='weathers_all')
WeatherAll.weathers = relationship('Weather',
                                   secondary=weather_types,
                                   back_populates='weathers')

def add_record(weather_all_params, data):
    engine = create_engine('sqlite:///' + Settings.options['db_name'], echo=False)
    if not engine.dialect.has_table(engine, 'weather_all'):
        Base.metadata.create_all(engine)
        model_logger.info('created new database {}'.format(Settings.options['db_name']))
    Session = sessionmaker(bind=engine)
    session = Session()
    data_location = {'lon': data['coord']['lon'],
                     'lat': data['coord']['lat'],
                     'name': data['name'],
                     'city_id': data['id']}
    loation_count = session.query(Location).filter_by(name=data_location['name']).count()
    if loation_count == 0:
        location = Location(**data_location)
    else:
        location = session.query(Location).filter_by(name=data_location['name']).one()
    location.weathers_all.append(WeatherAll(**weather_all_params))
    session.add(location)
    last_weather = session.query(WeatherAll).order_by(desc(WeatherAll.id)).first()
    for weather in data['weather']:
        weather_count = session.query(Weather).filter_by(id=weather['id']).count()
        if weather_count != 0:
            continue
        last_weather.weathers.append(Weather(**weather))
    session.commit()
    session.close()
    model_logger.info('added new record to db')
