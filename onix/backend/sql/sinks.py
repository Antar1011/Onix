"""Sink implementations for SQL backend"""
import hashlib

from onix import dto
from onix.dto import Moveset
from onix.utilities import compute_sid
from onix.collection import sinks as _sinks
from onix.backend.sql import model


def compute_tid(team, sanitizer=None):
    """
    Computes the Team ID for the given group of movesets

    Args:
        team (:obj:`iterable` of :obj:`Moveset` or :obj:`str`) :
            the team for which to compute the TID, represented either by their
            movesets or by their SIDs
        sanitizer (:obj:`onix.utilities.Sanitizer`, optional):
            if no sanitizer is provided, movesets are assumed to be already
            sanitized. Otherwise, the provided ``Sanitizer`` is used to sanitize
            the movesets.

    Returns:
        str: the corresponding Team ID

    Examples:
        >>> from onix.dto import Moveset, Forme, PokeStats
        >>> from onix.backend.sql.sinks import compute_tid
        >>> delphox = Moveset([Forme('delphox', 'magician',
        ...                    PokeStats(282, 158, 222, 257, 220, 265))],
        ...                   'f', 'lifeorb', ['calmmind', 'psychic'], 100, 255)
        >>> ditto = Moveset([Forme('ditto', 'imposter',
        ...                  PokeStats(259, 164, 98, 134, 126, 123))],
        ...                  'u', 'focussash', ['transform'], 100, 255)
        >>> print(compute_tid([delphox, ditto])) #doctest: +ELLIPSIS
        4e49b0eb...
    """
    if isinstance(team[0], Moveset):
        sids = [compute_sid(moveset, sanitizer) for moveset in team]
    elif isinstance(team[0], str):
        sids = team
    else:
        raise TypeError('team is neither an iterable of movesets nor SIDs')
    sids = sorted(sids)
    team_hash = hashlib.sha512(repr(sids).encode('utf-8')).hexdigest()

    # may eventually want to truncate hash, e.g.
    # team_hash = team_hash[:16]

    return team_hash


def compute_fid(forme, sanitizer=None):
    """
    Computes the Forme ID for a given forme

    Args:
        forme (dto.Forme) : the forme to compute the FID for.
        sanitizer (:obj:`onix.utilities.Sanitizer`, optional):
            if no sanitizer is provided, the forme is assumed to be already
            sanitized. Otherwise, the provided ``Sanitizer`` is used to sanitize
            the forme.

    Returns:
        str : the corresponding Forme ID

    Examples:
        >>> from onix.dto import Forme, PokeStats
        >>> from onix.backend.sql.sinks import compute_fid
        >>> forme = Forme('stunfisk', 'static',
        ...               PokeStats(369, 168, 177, 258, 225, 73))
        >>> print(compute_fid(forme)) #doctest: +ELLIPSIS
        2220c1624d...
    """
    if sanitizer is not None:
        forme = sanitizer.sanitize(forme)
    forme_hash = hashlib.sha512(repr(forme).encode('utf-8')).hexdigest()

    # may eventually want to truncate hash, e.g.
    # forme_hash = forme_hash[:16]

    return forme_hash


def convert_forme(forme_dto):
    """
    Converts a Forme DTO to the corresponding ORM object

    Args:
        forme_dto (dto.Forme) : the forme to convert. Is assumed to be
            sanitized.

    Returns:
        model.Forme : the corresponding ORM object

    Examples:
        >>> from onix.dto import Forme, PokeStats
        >>> from onix.backend.sql.sinks import convert_forme
        >>> forme = Forme('heatmor', 'gluttony',
        ...               PokeStats(333, 241, 170, 253, 150, 204))
        >>> db_obj = convert_forme(forme)
        >>> print(db_obj.atk)
        241
    """
    return model.Forme(id=compute_fid(forme_dto),
                       species=forme_dto.species,
                       ability=forme_dto.ability,
                       hp=forme_dto.stats.hp, atk=forme_dto.stats.atk,
                       dfn=forme_dto.stats.dfn, spa=forme_dto.stats.spa,
                       spd=forme_dto.stats.spd, spe=forme_dto.stats.spe)


def convert_moveset(moveset_dto):
    """
    Converts a Moveset DTO to the corresponding ORM object

    Args:
        moveset_dto (dto.Moveset) : the moveset to convert. Is assumed to be
            sanitized.

    Returns:
        model.Moveset : the corresponding ORM object, including any child
            classes

    Examples:
        >>> from onix.dto import Moveset, Forme, PokeStats
        >>> from onix.backend.sql.sinks import convert_moveset
        >>> moveset = Moveset([Forme('diglett', 'sandveil',
        ...                    PokeStats(17, 11, 9, 11, 10, 17))],
        ... 'm', 'leftovers',
        ... ['earthquake', 'rockslide', 'shadowclaw', 'substitute'], 5, 255)
        >>> db_obj = convert_moveset(moveset)
        >>> print(db_obj.moves) #doctest: +ELLIPSIS
        [<onix.backend.sql.model._Move object at...>, ...]
        >>> print(db_obj.moves[0].move)
        earthquake
    """
    return model.Moveset(id=compute_sid(moveset_dto),
                         gender=moveset_dto.gender, item=moveset_dto.item,
                         level=moveset_dto.level,
                         happiness=moveset_dto.happiness,
                         moves=[model._Move(idx=i, move=move)
                                for i, move in enumerate(moveset_dto.moves)],
                         formes=[convert_forme(forme)
                                 for forme in moveset_dto.formes])


def convert_team(team_sids):
    """
    Converts a list of SIDs specifying a player's team into the corresponding
    ORM objects

    Args:
        team_sids (:obj:`list` of :obj:`str`) : the SIDs corresponding to a
            player's pokemon

    Returns:
        (tuple) :
            * str : the TID uniquely specifying the team
            * :obj:`list` of :obj:`model.TeamMember` : the corresponding ORM
                objects

    Examples:
        >>> from onix.backend.sql.sinks import convert_team
        >>> tid, db_objs = convert_team(['ghi', 'abc', 'def'])
        >>> print(tid) #doctest +ELLIPSIS
        8711a93...
        >>> print(db_objs[1].sid)
        def

    """

    team_sids.sort()
    tid = compute_tid(team_sids)
    members = [model.TeamMember(tid=tid, idx=i, sid=sid)
               for i, sid in enumerate(team_sids)]

    return tid, members


def convert_player(player_dto, side, tid):
    """
    Converts a Player DTO to the corresponding ORM object

    Args:
        player_dto (dto.Player) : the Player to convert

        side (int) : the player's "index" in the battle.

            .. note::
                this index is one-based rahter than zero-based, so as to
                maintain consistency with log references (*i.e.* "player 1 vs.
                player 2").

        tid (str) : the TID for the player's team

    Returns:
        model.BattlePlayer : the corresponding ORM object

    Examples:
        >>> from onix.dto import Player
        >>> from onix.backend.sql.sinks import convert_player
        >>> player = Player(id='chaos', rating={'elo': 1311.1479745117863,
        ...                                     'rpr': None,
        ...                                      'r': 1227.7501280633721,
        ...                                      'l': 83, 'rprd': None,
        ...                                      'rd': 129.53915739500627,
        ...                                      'w': 40})
        >>> db_obj = convert_player(player, 1, 'aac491ca1')
        >>> print(db_obj.w)
        40
        >>> print(db_obj.t)
        None
        >>> print(db_obj.rpr)
        None
    """

    return model.BattlePlayer(side=side, pid=player_dto.id, tid=tid,
                              **player_dto.rating)


def convert_battle_info(battle_info_dto):
    """
    Converts a BattleInfo DTO to the corresponding ORM objects

    Args:
        battle_info_dto (dto.BattleInfo) : the BattleInfo to convert

    Returns:
        (tuple) :
            * model.BattleInfo : the corresponding ORM object, including any
                child classes
            * :obj:`list` of :obj:`model.TeamMember` : ORM representations of
                the team members for all player's teams

    Examples:
        >>> import datetime
        >>> from onix.dto import BattleInfo, Player
        >>> from onix.backend.sql.sinks import convert_battle_info
        >>> battle_info = BattleInfo(5776, 'randombattle',
        ...                          datetime.date(2016, 9, 21),
        ...                          [Player('echad', {'w': 1, 'l': 0}),
        ...                           Player('shtaymin', {'w': 0, 'l': 1})],
        ...                          [['abc', 'cab', 'bac'],
        ...                           ['123', '312', '213']], 16, 'forfeit')
        >>> db_objs = convert_battle_info(battle_info)
        >>> print(db_objs[0].players[0].side) #doctest +ELLIPSIS
        1
        >>> print(db_objs[0].players[0].tid) #doctest +ELLIPSIS
        267e429f...
        >>> print(db_objs[1][0].tid)
        267e429f...
    """
    teams = [convert_team(team) for team in battle_info_dto.slots]
    db_battle_info = model.BattleInfo(id=battle_info_dto.id,
                                      format=battle_info_dto.format,
                                      date=battle_info_dto.date,
                                      turns=battle_info_dto.turn_length,
                                      end_type=battle_info_dto.end_type,
                                      players=[convert_player(player, i + 1,
                                                              teams[i][0])
                                               for i, player
                                               in enumerate(
                                              battle_info_dto.players)])
    members = sum([team for (tid, team) in teams], [])
    return db_battle_info, members


class MovesetSink(_sinks.MovesetSink):
    """
    SQL implementation of the MovesetSink interface

    Args:
            session_maker (sa.orm.session.sessionmaker) :
                the session factory used to generate the session that will
                be used to communicate with the database
            batch_size (:obj:`int`, optional) :
                the number of movesets to go through before actually committing
                to the database
    """
    def __init__(self, session_maker, batch_size=1000):
        self.batch_size = batch_size
        self.session = session_maker()
        self.count = 0

    def flush(self):
        self.session.commit()
        self.count = 0

    def close(self):
        self.flush()
        self.session.close()

    def store_movesets(self, movesets):
        for moveset in movesets.values():
            self.session.add(convert_moveset(moveset))
            self.count += 1

        if self.count >= self.batch_size:
            self.flush()


class BattleInfoSink(_sinks.BattleInfoSink):
    """
    SQL implementation of the MovesetSink interface

    Args:
            session_maker (sa.orm.session.sessionmaker) :
                the session factory used to generate the session that will
                be used to communicate with the database
            batch_size (:obj:`int`, optional) :
                the number of battles to go through before actually committing
                to the database
    """
    def __init__(self, session_maker, batch_size=1000):
        self.batch_size = batch_size
        self.session = session_maker()
        self.count = 0

    def flush(self):
        self.session.commit()
        self.count = 0

    def close(self):
        self.flush()
        self.session.close()

    def store_battle_info(self, battle_info):
        db_battle_info, team_members = convert_battle_info(battle_info)
        self.session.add_all([db_battle_info] + team_members)
        self.count += 1

        if self.count >= self.batch_size:
            self.flush()
