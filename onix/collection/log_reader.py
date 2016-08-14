"""Functionality for taking PS logs & structuring them into a desired format"""

import abc
import json

from onix.dto import Moveset, Player
from onix import scrapers
from onix import utilities


def _is_a_mega_forme(species, pokedex):
    """
    Determines if a species is a mega forme.

    Args:
        species (str) : the species or forme name (sanitized)
        pokedex (dict) : data including base stats, species abilities and forme
            info

    Returns:
        bool : True if it's a mega forme, False if it's not

    """
    if 'baseSpecies' not in pokedex[species].keys():
        return False
    if species.endswith(('mega', 'megax', 'megay', 'primal')):
        return True
    return False


def rating_dict_to_player(rating_dict):
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
        >>> from onix.collection.log_reader import rating_dict_to_player
        >>> rating_dict = {'r': 1630, 'rd': 100, 'rpr': 1635, 'rprd': 95,
        ... 'w': 10, 'l': 3, 't': 0, 'cool_new_rating': 63.1,
        ... 'username': 'Testy McTestFace', 'userid': 'test'}
        >>> player = rating_dict_to_player(rating_dict)
        >>> player.player_id
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


class LogReader(object):
    """
    An object which takes in a Pokemon Showdown log (in whatever format it
    exists) and returned structured data, ready for compiling or storing
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def parse_log(self, log):
        """
        Parse the provided log and return structured data

        Args:
            log: the log to parse, in whatever format the reader can parse

        Returns:
            (tuple) :
                * BattleInfo : metadata about the match
                * :obj:`tuple` of :obj:`tuple` of :obj:`Moveset` : the movesets
                    used in the battle, grouped by team
                * Battle : a structured turn-by-turn recounting of the battle

        Raises:
            ParsingException: if there's a problem parsing the log

        """


class JsonFileLogReader(LogReader):
    """
    Parses Pokemon Showdown ``.json`` files

    Args:
        sanitizer (:obj:`Sanitizer`, optional) :
            used to normalize the data read in from the log. If none is
                specified, will create its own
        pokedex (:obj:`dict`, optional) :
            data including base stats, species abilities and forme info. If
            none is specified will attempt to load from file, and if the
            file doesn't exist will scrape the data from the Pokemon
            Showdown GitHub
        items (:obj:`dict`, optional) :
            used for determining mega stones. If none is specified will
            attempt to load from file, and if the file doesn't exist will
            scrape it from the Pokemon Showdown GitHub
        """

    def __init__(self, sanitizer=None, pokedex=None, items=None):

        if sanitizer is None:
            sanitizer = utilities.Sanitizer()
        if pokedex is None:
            try:
                pokedex = json.load(open('.psdata/pokedex.json'))
            except IOError:
                pokedex = scrapers.scrape_battle_pokedex()
        if items is None:
            try:
                items = json.load(open('.psdata/items.json'))
            except IOError:
                items = scrapers.scrape_battle_items()

        self.sanitizer = sanitizer
        self.pokedex = pokedex
        self.items = items
        self.natures = utilities.load_natures()

        # diagnostics
        self.devolve_count = 0
        self.battle_forme_undo_count = 0
        self.ability_correct_count = 0
        self.hidden_power_no_type = 0
        self.hidden_power_wrong_type = 0

    def parse_log(self, log):
        """
        Parse the provided log and return structured data

        Args:
            log (str) : file name of the battle log to parse

        Returns:
            (tuple):
                * BattleInfo : metadata about the match
                * :obj:`tuple` of :obj:`tuple` of :obj:`Moveset` : the movesets
                    used in the battle, grouped by team
                * Battle : a structured turn-by-turn recounting of the battle

        Raises:
            ParsingException : if there's a problem parsing the log
            FileNotFoundError : if the log doesn't exist
            json.decoder.JSONDecodeError : if the log is not a valid log

        """

        log = json.load(open(log))
        pass

    def _parse_moveset(self, moveset_dict, hackmons=False,
                       any_ability=False,
                       mega_rayquaza_allowed=True):
        """
        Make a ``Moveset`` from an entry in a Pokemon Showdown log

        Args:
            moveset_dict (dict) : the moveset dict as parsed from the log
            hackmons (:obj:`bool`, optional) : is this a Hackmons meta (where
                Pokemon can start in their mega formes)? Default is False.
            any_ability (:obj:`bool`, optional) : is this a Hackmons metagame or
                a metagame like Almost-Any-Ability? Default is False.
            mega_rayquaza_allowed (:obj:`bool`, optional) : is Mega Rayquaza
                allowed in this metagame? Default is True. Note that if
                base-Rayquaza isn't allowed, there's no sense in setting this
                flag to False.

        Returns:
            Moveset : the corresponding moveset

        """
        species = self.sanitizer.sanitize(moveset_dict['species'])
        ability = self.sanitizer.sanitize(moveset_dict['ability'])
        moves = self.sanitizer.sanitize(moveset_dict['moves'])
        ivs = utilities.stats_dict_to_dto(moveset_dict['ivs'])
        moves = self._normalize_hidden_power(moves, ivs)

        item = moveset_dict['item']
        if item == '':
            item = None

        species = self._normalize_mega_evolution(species, item, moves, hackmons,
                                                 mega_rayquaza_allowed)
        species = self._normalize_battle_formes(species)
        ability = self._normalize_ability(species, ability, any_ability)

        gender = self.sanitizer.sanitize(moveset_dict.get('gender', 'u'))
        level = moveset_dict.get('level', 100)
        happiness = moveset_dict.get('happiness', 255)

        base_stats = utilities.stats_dict_to_dto(
            self.pokedex[species]['baseStats'])
        evs = utilities.stats_dict_to_dto(moveset_dict['evs'])
        nature = self.natures[self.sanitizer.sanitize(moveset_dict['nature'])]

        stats = utilities.calculate_stats(base_stats, nature, ivs, evs, level)

        return Moveset(species, ability, gender, item, moves, stats, level,
                       happiness)  # moveset should be fully sanitized

    def _normalize_mega_evolution(self, species, item, moves,
                                  hackmons=False, mega_rayquaza_allowed=True):
        """
        We want (or at least want to be able to) count mega Pokemon separately
        from their base formes. So this function facilitates "mega evolving"
        base formes which can mega evolve during battle. It also "devolves"
        instances where the mega forme is specified as the species but, say,
        it's not actually holding the correct mega stone. Pokemon Showdown
        *should* devolve automatically, but we check just in case (and note it
        if it happens).

        Args:
            species (str) : the sanitized species
            item (str) : the sanitized held item
            moves (list[str]) : the sanitized moves
            hackmons (:obj:`bool`, optional) : is this a Hackmons meta (where
                Pokemon can start in their mega formes)? Default is False.
            mega_rayquaza_allowed (:obj:`bool`, optional) : is Mega Rayquaza
                allowed in this metagame? Default is True. Note that if
                base-Rayquaza isn't allowed, there's no sense in setting this
                flag to False.

        Returns:
            str : the sanitized species
        """

        if hackmons:  # for Hackmons metas, the species in the log is king
            return species

        if species.startswith('rayquaza'):  # handle Rayquaza separately
            if mega_rayquaza_allowed and 'dragonascent' in moves:
                correct_species = 'rayquazamega'
            else:
                correct_species = 'rayquaza'
            if species != correct_species:
                if correct_species == 'rayquaza':
                    self.devolve_count += 1
            return correct_species

        if item is None:
            item = dict()
        elif item == 'redorb':  # manual fix
            item = {'megaEvolves': 'groudon', 'megaStone': 'groudonprimal'}
        elif item == 'blueorb':  # manual fix
            item = {'megaEvolves': 'kyogre', 'megaStone': 'kyogreprimal'}
        else:
            item = self.items[item]

        if 'megaStone' not in item.keys():  # devolve if no mega stone
            if _is_a_mega_forme(species, self.pokedex):
                self.devolve_count += 1
                return self.sanitizer.sanitize(
                    self.pokedex[species]['baseSpecies'])
            return species

        base_species = self.sanitizer.sanitize(item['megaEvolves'])
        mega_species = self.sanitizer.sanitize(item['megaStone'])

        if _is_a_mega_forme(species, self.pokedex) and species != mega_species:
            '''devolve if the mega species doesn't match the stone'''
            self.devolve_count += 1
            return self.sanitizer.sanitize(self.pokedex[species]['baseSpecies'])
        elif species == base_species:
            '''evolve if mega stone matches the base species'''
            return mega_species

        return species

    def _normalize_battle_formes(self, species):
        """
        Darmanitan-Zen and Meloetta-Pirouette aren't allowed in any metagame, so
        if you see it, replace it with its base form (and note that it showed
        up)

        Args:
            species (str) : the species to normalize
        Returns:
            str : the normalized species
        """
        if species in ('darmanitanzen', 'meloettapirouette'):
            self.battle_forme_undo_count += 1
            return self.sanitizer.sanitize(
                self.pokedex[species]['baseSpecies'])
        return species

    def _normalize_ability(self, species, ability, any_ability=False):
        """
        So while we are treating Mega formes separately for counting, we still
        want to note the base forme's ability. That subtlety means we might need
        to *normalize* a moveset to make sure that the ability is a base forme
        ability (and not a mega forme ability). Pokemon Showdown should be
        doing this automatically, but we check just in case (and note it
        if we need to perform a correction).

        Args:
            species (str) : the sanitized species
            ability (str) : the sanitized ability
            any_ability (:obj:`bool`, optional) : is this a Hackmons metagame or
                a metagame like Almost-Any-Ability? Default is False.

        Returns:
            str : the normalized ability
        """

        if any_ability:  # movesets for these metas don't require normalization
            return ability

        if _is_a_mega_forme(species, self.pokedex):
            species = self.sanitizer.sanitize(
                self.pokedex[species]['baseSpecies'])

        if ability in self.sanitizer.sanitize(
                self.pokedex[species]['abilities'].values()):
            return ability  # no normalization needed

        self.ability_correct_count += 1
        return self.sanitizer.sanitize(self.pokedex[species]['abilities']['0'])

    def _normalize_hidden_power(self, moves, ivs):
        """
        In theory, Pokemon Showdown sets the correct Hidden Power type from the
        IVs and represents Hidden Power in the moveset as the specifically-typed
        Hidden Power. But it's best not to assume such things, so let's
        calculate it ourselves

        Args:
            moves (:obj:`list` of :obj:`str`) : the moves the Pokemon knows
            ivs (PokeStats) : the Pokemon's Indiviual Values

        Returns:
            :obj:`list` of :obj:`str` : sanitized move list, with Hidden Power
                (if present) correctly typed
        """
        for i in range(len(moves)):
            move = moves[i]
            if move.startswith('hiddenpower'):
                correct_type = utilities.determine_hidden_power_type(ivs)
                correct_hp = 'hiddenpower{0}'.format(correct_type)

                if move != correct_hp:
                    if move == 'hiddenpower':
                        self.hidden_power_no_type += 1
                    else:
                        self.hidden_power_wrong_type += 1
                    moves[i] = correct_hp
                break
        return moves