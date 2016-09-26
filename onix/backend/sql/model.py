"""Table structure for SQL Backend"""
import sqlalchemy as sa


# SQLite foreign key enforcement derived from: https://goo.gl/okJmTL
@sa.event.listens_for(sa.engine.Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

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

metadata = sa.MetaData()

# moveset info that's shared across formes
movesets = sa.Table('movesets', metadata,
                    sa.Column('id', sa.String(512), primary_key=True),
                    sa.Column('gender', sa.CHAR),
                    sa.Column('item', sa.String(64)),
                    sa.Column('level', sa.SmallInteger),
                    sa.Column('happiness', sa.SmallInteger))

# moves
moveslots = sa.Table('moveslots', metadata,
                     sa.Column('sid', sa.String(512),
                               sa.ForeignKey('movesets.id'), primary_key=True),
                     sa.Column('idx', sa.SmallInteger, primary_key=True),
                     sa.Column('move', sa.String(64)))
'''Note that the "idx" column refers to the position of the move after
sorting / sanitizing and doesn't reflect the actual position of the move'''

# forme info
formes = sa.Table('formes', metadata,
                  sa.Column('id', sa.String(512), primary_key=True),
                  sa.Column('species', sa.String(64), nullable=False),
                  sa.Column('ability', sa.String(64)),
                  sa.Column('hp', sa.SmallInteger),
                  sa.Column('atk', sa.SmallInteger),
                  sa.Column('dfn', sa.SmallInteger),
                  sa.Column('spa', sa.SmallInteger),
                  sa.Column('spd', sa.SmallInteger),
                  sa.Column('spe', sa.SmallInteger))

# association table for many-to-many mappings of movesets to formes
moveset_forme_table = sa.Table('moveset_forme', metadata,
                               sa.Column('sid', sa.String(512),
                                         sa.ForeignKey('movesets.id'),
                                         primary_key=True),
                               sa.Column('fid', sa.String(512),
                                         sa.ForeignKey('formes.id'),
                                         primary_key=True),
                               sa.Column('primary', sa.Boolean))

# team members
teams = sa.Table('teams', metadata,
                 sa.Column('tid', sa.String(512), primary_key=True),
                 sa.Column('idx', sa.SmallInteger, primary_key=True),
                 sa.Column('sid', sa.String(512), nullable=False))
'''
Note that the "idx" column refers to the position of the member after sorting
the team by SID, *not* its position on a team during battle.

Note also that the sid column should really be a foreign key in the movesets
table, but it's not so as to allow movesets and battle info to be written to the
DB in any order. Be aware, and take special care to preserve preserve the
integrity of this table.
'''

# battle metadata
battle_infos = sa.Table('battle_infos', metadata,
                        sa.Column('id', sa.Integer, primary_key=True),
                        sa.Column('format', sa.String(64)),
                        sa.Column('date', sa.Date),
                        sa.Column('turn', sa.Integer),
                        sa.Column('end_type', sa.String(64)))

# player-instance metadata
battle_players = sa.Table('battle_players', metadata,
                          sa.Column('bid', sa.Integer,
                                    sa.ForeignKey('battle_infos.id'),
                                    primary_key=True),
                          sa.Column('side', sa.SmallInteger, primary_key=True),
                          sa.Column('pid', sa.String(512), nullable=False),
                          sa.Column('tid', sa.String(512),
                                    sa.ForeignKey('teams.tid')),
                          sa.Column('w', sa.Integer),
                          sa.Column('l', sa.Integer),
                          sa.Column('t', sa.Integer),
                          sa.Column('elo', sa.Float),
                          sa.Column('r', sa.Float),
                          sa.Column('rd', sa.Float),
                          sa.Column('rpr', sa.Float),
                          sa.Column('rprd', sa.Float))

'''
It's possible that in the future we'll have a table that we don't want to
ignore, but for now...'''
_ignore_tables.update(metadata.tables.keys())

def create_tables(engine):
    """
    Creates all the tables for the SQL backend

    Args:
        engine (sqlalchemy.engine.base.Engine) : the database engine to use

    Returns:
        None

    """
    metadata.create_all(engine)
