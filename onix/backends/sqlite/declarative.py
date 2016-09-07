"""Declarative class definitions for SQLite Backend"""
import sqlalchemy as sq
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Moveset(Base):
    __tablename__ = 'movesets'

    id = sq.Column(sq.String(512), primary_key=True)
    gender = sq.Column(sq.CHAR)
    item = sq.Column(sq.String(64))
    level = sq.Column(sq.SmallInteger)
    happiness = sq.Column(sq.SmallInteger)

    formes = relationship('Forme', secondary=moveset_forme_table)
    moves = relationship('Move')


class Forme(Base):
    __tablename__ = 'formes'

    id = sq.Column(sq.String(512), primary_key=True)
    species = sq.Column(sq.String(64), nullable=False)
    ability = sq.Column(sq.String(64))
    hp = sq.Column(sq.SmallInteger)
    atk = sq.Column(sq.SmallInteger)
    dfn = sq.Column(sq.SmallInteger)
    spa = sq.Column(sq.SmallInteger)
    spd = sq.Column(sq.SmallInteger)
    spe = sq.Column(sq.SmallInteger)

    movesets = relationship('Moveset', secondary=moveset_forme_table)

moveset_forme_table = sq.Table('moveset_forme', Base.metadata,
                               sq.Column('sid', sq.String(512),
                                         sq.ForeignKey('movesets.id')),
                               sq.Column('fid', sq.String(512),
                                         sq.ForeignKey('formes.id')))


class Move(Base):
    __tablename__ = 'moveslots'

    _id = sq.Column(sq.Integer, primary_key=True)
    sid = sq.Column(sq.String(512), sq.ForeignKey('movesets.id'))
    move = sq.Column(sq.String(64))


class Team(Base):
    __tablename__ = 'teams'

    _id = sq.Column(sq.Integer, primary_key=True)
    tid = sq.Column(sq.String(512), primary_key=True)
    sid = sq.Column(sq.String(512), sq.ForeignKey('movesets.id'),
                    nullable=False)


class BattleInfo(Base):
    __tablename__ = 'battle_info'

    id = sq.Column(sq.Integer, primary_key=True)
    format = sq.Column(sq.String(512))
    date = sq.Column(sq.Date)
    turns = sq.Column(sq.Integer)
    end_type = sq.Column(sq.String(64))

    players = relationship('BattlePlayer', order_by='BattlePlayer.side')


class BattlePlayer(Base):
    __tablename__ = 'battle_player'

    bid = sq.Column(sq.Integer, sq.ForeignKey('battle_info.id'),
                    primary_key=True)
    side = sq.Column(sq.SmallInteger, primary_key=True)

    pid = sq.Column(sq.String(512), nullable=False)
    tid = sq.Column(sq.String(512), nullable=False)

    w = sq.Column(sq.Integer)
    l = sq.Column(sq.Integer)
    t = sq.Column(sq.Integer)
    elo = sq.Column(sq.Float)
    r = sq.Column(sq.Float)
    rd = sq.Column(sq.Float)
    rpr = sq.Column(sq.Float)
    rprd = sq.Column(sq.Float)

