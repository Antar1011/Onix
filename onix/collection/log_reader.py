"""Functionality for taking PS logs & structuring them into a desired format"""

import abc
import json

import six

from onix.dto import Moveset, Player
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


class LogReader(six.with_metaclass(abc.ABCMeta, object)):
    """
    An object which takes in a Pokemon Showdown log (in whatever format it
    exists) and returned structured data, ready for compiling or storing. The
    intent is for a separate `LogReader` to be instantiated for each metagame
    that's being processed

    Args:
        metagame (str):
            the name of the tier/metagame
        sanitizer (Sanitizer):
            used to normalize the data read in from the log
        pokedex (dict):
            data including base stats, species abilities and forme info, scraped
            from Pokemon Showdown
        items (dict):
            used for determining mega stones, scraped from Pokemon Showdown
        formats (dict):
            used for determining the rulesets that apply to the metagame.
            Scraped from Pokemon Showdown, with some significant post-processing
    """

    def __init__(self, metagame, sanitizer, pokedex, items, formats):

        self.metagame = metagame
        self.sanitizer = sanitizer
        self.pokedex = pokedex
        self.items = items
        self.natures = utilities.load_natures()

        (self.game_type,
         self.hackmons,
         self.any_ability,
         self.mega_rayquaza_allowed) = utilities.parse_ruleset(
            formats[self.metagame])

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
                * :obj:`tuple` of :obj:`tuple` of :obj:`Moveset` : the movesets
                    used in the battle, grouped by team
                * Battle : a structured turn-by-turn recounting of the battle

        Raises:
            ParsingException: if there's a problem parsing the log
        """
        log = self._parse_log(log_ref)

    def _parse_moveset(self, moveset_dict):
        """
        Make a ``Moveset`` from an entry in a Pokemon Showdown log

        Args:
            moveset_dict (dict) : the moveset dict as parsed from the log

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

    def _get_all_formes(self, species, ability, item, moves):
        """Get all formes a Pokemon might appear as during a battle

        Args:
            species (str): the species (as represented in the Showdown log)
            ability (str): the Pokemon's ability
            item (str): the held item
            moves (:obj:`list` of :obj:`str`): sanitized list of moves
        Returns:
            :obj:`list` of :obj:`Forme`s: the formes the Pokemon might take on
                during a battle. Note that the `stats` item represents base
                stats, not battle stats
        """
        if self.hackmons:



    def _normalize_mega_evolution(self, species, item, moves):
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



class JsonFileLogReader(LogReader):
    """
    Parses Pokemon Showdown ``.json`` files

    Args:
        metagame (str):
            the name of the tier/metagame
        sanitizer (Sanitizer):
            used to normalize the data read in from the log
        pokedex (dict):
            data including base stats, species abilities and forme info, scraped
            from Pokemon Showdown
        items (dict):
            used for determining mega stones, scraped from Pokemon Showdown
        formats (dict):
            used for determining the rulesets that apply to the metagame.
            Scraped from Pokemon Showdown, with some significant post-processing
        log_folder (str):
            file folder where the logs are stored for the month)
    """
    def __init__(self, metagame, sanitizer, pokedex, items, formats,
                 log_folder):
        super(JsonFileLogReader, self).__init__(metagame, sanitizer, pokedex,
                                                items, formats)
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
        return json.load(open('{0}/{1}/{2}'.format(self.log_folder,
                                                   self.metagame,
                                                   log_ref)))
