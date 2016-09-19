"""Declarative class definitions for SQL Backend"""
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

_ignore_tables = set()


# INSERT OR IGNORE handling derived from: http://goo.gl/ih2NbY
@sa.event.listens_for(sa.engine.Engine, "before_execute", retval=True)
def _ignore_insert(conn, element, multiparams, params):
    if isinstance(element, sa.sql.Insert) \
            and element.table.name in _ignore_tables:
        element = element.prefix_with("OR IGNORE")
    return element, multiparams, params


def ignore_inserts(cls):
    _ignore_tables.add(cls.__table__.name)
    return cls

# association table for many-to-many mappings of movesets to formes
moveset_forme_table = sa.Table('moveset_forme', Base.metadata,
                               sa.Column('sid', sa.String(512),
                                         sa.ForeignKey('movesets.id')),
                               sa.Column('fid', sa.String(512),
                                         sa.ForeignKey('formes.id')))


@ignore_inserts
class Moveset(Base):
    """
    ORM representation of a Moveset object
    """
    __tablename__ = 'movesets'

    id = sa.Column(sa.String(512), primary_key=True)
    gender = sa.Column(sa.CHAR)
    item = sa.Column(sa.String(64))
    level = sa.Column(sa.SmallInteger)
    happiness = sa.Column(sa.SmallInteger)

    formes = relationship('Forme', secondary=moveset_forme_table)
    moves = relationship('Move')


@ignore_inserts
class Forme(Base):
    """
    ORM representation of a Forme object
    """
    __tablename__ = 'formes'

    id = sa.Column(sa.String(512), primary_key=True)
    species = sa.Column(sa.String(64), nullable=False)
    ability = sa.Column(sa.String(64))
    hp = sa.Column(sa.SmallInteger)
    atk = sa.Column(sa.SmallInteger)
    dfn = sa.Column(sa.SmallInteger)
    spa = sa.Column(sa.SmallInteger)
    spd = sa.Column(sa.SmallInteger)
    spe = sa.Column(sa.SmallInteger)

    movesets = relationship('Moveset', secondary=moveset_forme_table)


class _Move(Base):
    """
    ORM representation of a move on a moveset. Should not be accessed directly.
    Note that the "idx" column refers to the position of the move after
    sorting / sanitizing and doesn't reflect the actual position of the move
    """
    __tablename__ = 'moveslots'

    sid = sa.Column(sa.String(512), sa.ForeignKey('movesets.id'),
                    primary_key=True)
    idx = sa.Column(sa.SmallInteger, primary_key=True)
    move = sa.Column(sa.String(64))


class TeamMember(Base):
    """
    ORM representation of a team member. Note that the "idx" column refers to
    the position of the member after sorting the team by SID, *not* its position
    on a team during battle.
    """
    __tablename__ = 'teams'

    tid = sa.Column(sa.String(512), primary_key=True)
    idx = sa.Column(sa.SmallInteger, primary_key=True)
    sid = sa.Column(sa.String(512), sa.ForeignKey('movesets.id'),
                    nullable=False)


@ignore_inserts
class BattleInfo(Base):
    """
    ORM representation of a BattleInfo object
    """
    __tablename__ = 'battle_info'

    id = sa.Column(sa.Integer, primary_key=True)
    format = sa.Column(sa.String(512))
    date = sa.Column(sa.Date)
    turns = sa.Column(sa.Integer)
    end_type = sa.Column(sa.String(64))

    players = relationship('BattlePlayer', order_by='BattlePlayer.side')


@ignore_inserts
class BattlePlayer(Base):
    """
    ORM representation of a Player object
    """
    __tablename__ = 'battle_player'

    bid = sa.Column(sa.Integer, sa.ForeignKey('battle_info.id'),
                    primary_key=True)
    side = sa.Column(sa.SmallInteger, primary_key=True)

    pid = sa.Column(sa.String(512), nullable=False)
    tid = sa.Column(sa.String(512), nullable=False)

    w = sa.Column(sa.Integer)
    l = sa.Column(sa.Integer)
    t = sa.Column(sa.Integer)
    elo = sa.Column(sa.Float)
    r = sa.Column(sa.Float)
    rd = sa.Column(sa.Float)
    rpr = sa.Column(sa.Float)
    rprd = sa.Column(sa.Float)

