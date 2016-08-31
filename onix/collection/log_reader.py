"""Functionality for taking PS logs & structuring them into a desired format"""

import abc
import datetime
import json

import six

from onix.dto import Moveset, Forme, BattleInfo, Player
from onix import contexts
from onix import utilities


def get_all_formes(species, ability, item, moves,
                   context, hackmons=False, any_ability=False):
    """
    Get all formes a Pokemon might appear as during a battle

    Args:
        species (str) : the species (as represented in the Showdown log)
        ability (str) : the Pokemon's ability
        item (str) : the held item
        moves (:obj:`list` of :obj:`str`) : sanitized list of moves
        context (contexts.Context) : The resources needed by the function.
            Requires pokedex, accessible_formes and sanitizer.
        hackmons (:obj:`bool`, optional) :
            Set to True if this is for a metagame where a battle forme or mega
            evolution can appear outside its base forme. Default is False.
        any_ability (:obj:`bool`, optional) :
            Set to True if the Pokemon can have have "illegal" abilities.
            Default is False.

    Returns:
        :obj:`list` of :obj:`Forme`s: the formes the Pokemon might take on
            during a battle.

            .. note::
               The `stats` attribute represents base stats, not battle
               stats

    Examples:

    """
    # TODO: doctest

    contexts.require(context, 'pokedex', 'accessible_formes', 'sanitizer')

    # devolve (if not hackmons)
    if not hackmons:
        if 'baseSpecies' in context.pokedex[species].keys():
            species = context.sanitizer.sanitize(
                context.pokedex[species]['baseSpecies'])

    # lookup from accessible_formes
    other_formes = []
    if species in context.accessible_formes.keys():

        for conditions, formes in context.accessible_formes[species]:
            all_conditions_met = True
            for type, value in six.iteritems(conditions):
                if type == 'ability':
                    if value != ability:
                        all_conditions_met = False
                        break
                elif type == 'item':
                    if value != item:
                        all_conditions_met = False
                        break
                elif type == 'move':
                    if value not in moves:
                        all_conditions_met = False
                        break
                else:
                    raise ValueError('Condition "{0}" not recognized'
                                     .format(type))
            if all_conditions_met:
                other_formes += formes

    # create formes (look up abilities, base stats)
    formes = []
    dex_entry = context.pokedex[species]
    if not any_ability:
        abilities = context.sanitizer.sanitize(dex_entry['abilities'])
        if ability in abilities.values():
            forme_ability = ability
        else:
            forme_ability = abilities['0']
    else:
        forme_ability = ability
    stats = utilities.stats_dict_to_dto(dex_entry['baseStats'])
    formes.append(Forme(species, forme_ability, stats))

    for forme in other_formes:
        dex_entry = context.pokedex[forme]
        abilities = context.sanitizer.sanitize(dex_entry['abilities'])
        if ability in abilities.values():
            forme_ability = ability
        else:
            forme_ability = abilities['0']
        stats = utilities.stats_dict_to_dto(dex_entry['baseStats'])
        formes.append(Forme(forme, forme_ability, stats))
    return formes


def rating_dict_to_dto(rating_dict):
    """
    Make a ``Player`` from an entry in a Pokemon Showdown log

    Args:
        rating_dict (dict) : the ratings dict as parsed from the log

    Returns:
        Player : the corresponding Player

    Notes:
        If a relevant rating is missing from the ``rating_dict``, it will
        be represented in the resulting ``Player`` as ``None``.

    Examples:
        >>> import six
        >>> from onix.dto import Player
        >>> from onix.collection.log_reader import rating_dict_to_dto
        >>> rating_dict = {'r': 1630, 'rd': 100, 'rpr': 1635, 'rprd': 95,
        ... 'w': 10, 'l': 3, 't': 0, 'cool_new_rating': 63.1,
        ... 'username': 'Testy McTestFace', 'userid': 'test'}
        >>> player = rating_dict_to_dto(rating_dict)
        >>> player.id
        'test'
        >>> sorted(six.iteritems(player.rating)) #doctest: +NORMALIZE_WHITESPACE
        [('elo', None), ('l', 3.0), ('r', 1630.0), ('rd', 100.0),
        ('rpr', 1635.0), ('rprd', 95.0), ('t', 0.0), ('w', 10.0)]
    """

    ratings = dict()
    for metric in ('w', 'l', 't',  # these are fairly obvious
                   'elo',  # Zarel's modified Elo rating
                   'r', 'rd',  # Glicko ratings (at end of last period)
                   'rpr', 'rprd'  # projected Glicko ratings
                   ):
        value = None
        if metric in rating_dict:
            value = float(rating_dict[metric])
        ratings[metric] = value

    return Player(rating_dict['userid'],
                  ratings)


def _normalize_hidden_power(moves, ivs):
    """
    In theory, Pokemon Showdown sets the correct Hidden Power type from the
    IVs and represents Hidden Power in the moveset as the specifically-typed
    Hidden Power. But it's best not to assume such things, so let's
    calculate it ourselves

    Args:
        moves (:obj:`list` of :obj:`str`) : the moves the Pokemon knows (should
            already be sanitized)
        ivs (PokeStats) : the Pokemon's Indiviual Values
    Returns:
        :obj:`list` of :obj:`str` : sanitized move list, with Hidden Power
            (if present) correctly typed

    Examples:
        >>> from onix.dto import PokeStats
        >>> from onix.collection.log_reader import _normalize_hidden_power
        >>> _normalize_hidden_power(['hiddenpower', 'roost', 'thunderbolt',
        ...                          'voltswitch'],
        ...                         PokeStats(31, 31, 31, 31, 31, 30))
        ['hiddenpowerice', 'roost', 'thunderbolt', 'voltswitch']
    """
    for i, _ in enumerate(moves):
        move = moves[i]
        if move.startswith('hiddenpower'):
            correct_type = utilities.determine_hidden_power_type(ivs)
            correct_hp = 'hiddenpower{0}'.format(correct_type)

            if move != correct_hp:
                moves[i] = correct_hp
            break
    return moves


class LogReader(six.with_metaclass(abc.ABCMeta, object)):
    """
    An object which takes in a Pokemon Showdown log (in whatever format it
    exists) and returned structured data, ready for compiling or storing. The
    intent is for a separate `LogReader` to be instantiated for each metagame
    that's being processed

    Args:
        metagame (str) :
            the name of the tier/metagame
        context (onix.contexts.Context) :
            The resources needed by the log reader. Must have: pokedex, items,
            formats, sanitizer, accessible_formes and natures
    """

    def __init__(self, metagame, context):
        contexts.require(context, 'sanitizer', 'pokedex', 'items', 'formats',
                         'natures', 'accessible_formes')

        self.metagame = metagame
        self.context = context

        (self.game_type,
         self.hackmons,
         self.any_ability,
         self.mega_rayquaza_allowed) = utilities.parse_ruleset(
            self.context.formats[self.metagame])

    @abc.abstractmethod
    def _parse_log(self, log_ref):
        """
        Parse the specified log into a semi-structured format to be further
        structured and normalized by the ``parse_log`` method

        Args:
            log_ref: an identifier specifying the log to parse

        Returns:
            dict: the semi-structured log
        """

    def parse_log(self, log_ref):
        """
        Parses the provided log and returns structured and normalized data.

        Args:
            log_ref: an identifier specifying the log to parse

        Returns:
            (tuple):
                * BattleInfo : metadata about the match
                * :obj:`dict` of :obj:`str` to :obj:`Moveset` : a mapping of
                set IDs to movesets for the movesets appearing in the battle
                * Battle : a structured turn-by-turn recounting of the battle

        Raises:
            ParsingException: if there's a problem parsing the log
        """
        log = self._parse_log(log_ref)
        movesets = dict()
        players = []
        teams = []
        for player in ('p1', 'p2'):
            players.append(rating_dict_to_dto(log['{0}rating'
                                              .format(player)]))
            team = []
            for moveset_dict in log['{0}team'.format(player)]:
                moveset = self._parse_moveset(moveset_dict)
                set_id = utilities.compute_sid(moveset)
                team.append(set_id)
                movesets[set_id] = moveset
            teams.append(team)

        battle_info = BattleInfo(log['id'], self.metagame, log['date'], players,
                                 teams, log['turns'], log['endType'])

        return battle_info, movesets, None

    def _parse_moveset(self, moveset_dict):
        """
        Make a ``Moveset`` from an entry in a Pokemon Showdown log

        Args:
            moveset_dict (dict) : the moveset dict as parsed from the log

        Returns:
            Moveset : the corresponding moveset

        """
        species = self.context.sanitizer.sanitize(moveset_dict['species'])
        ability = self.context.sanitizer.sanitize(moveset_dict['ability'])
        gender = self.context.sanitizer.sanitize(
            moveset_dict.get('gender', 'u'))
        item = moveset_dict['item']
        moves = self.context.sanitizer.sanitize(moveset_dict['moves'])
        ivs = utilities.stats_dict_to_dto(moveset_dict['ivs'])
        evs = utilities.stats_dict_to_dto(moveset_dict['evs'])
        nature = self.context.natures[
            self.context.sanitizer.sanitize(moveset_dict['nature'])]
        level = moveset_dict.get('level', 100)
        happiness = moveset_dict.get('happiness', 255)

        if item == '':
            item = None
            moves = _normalize_hidden_power(moves, ivs)

        formes = get_all_formes(species, ability, item, moves,
                                self.context, self.hackmons,
                                self.any_ability)
        formes = self.context.sanitizer.sanitize([forme._replace(
            stats=utilities.calculate_stats(forme.stats, nature, ivs, evs,
                                            level)) for forme in formes])

        # moveset should be fully sanitized
        return Moveset(formes, gender, item, moves, level, happiness)


class JsonFileLogReader(LogReader):
    """
    Parses Pokemon Showdown ``.json`` files

    Args:
        metagame (str):
            the name of the tier/metagame
        context (onix.contexts.Context) :
            The resources needed by the log reader. Must have: pokedex, items,
            formats. sanitizer, accessible_formes and natures
        log_folder (str):
            file folder where the logs are stored for the month)
    """
    def __init__(self, metagame, context, log_folder):
        super(JsonFileLogReader, self).__init__(metagame, context)
        self.log_folder = log_folder

    def _parse_log(self, log_ref):
        """
        Parse the provided log and return structured data

        Args:
            log_ref (str) : file name of the battle log to parse, relative to
            [log_folder]/[metagame]/

        Returns:
            dict: the semi-structured log

        Raises:
            FileNotFoundError: if the log doesn't exist
            json.decoder.JSONDecodeError: if the log is not a valid log

        """
        log_dict = json.load(open('{0}/{1}/{2}'.format(self.log_folder,
                                                       self.metagame,
                                                       log_ref)))

        datestring = log_ref[:log_ref.find('/')].split('-')
        log_dict['date'] = datetime.date(int(datestring[0]),
                                         int(datestring[1]),
                                         int(datestring[2]))
        log_dict['id'] = int(log_ref[log_ref.rfind('-')+1: -9])
        return log_dict
