"""Functionality for taking PS logs & structuring them into a desired format"""

import abc
import json

from smogonusage.dto import *
from smogonusage import scrapers
from smogonusage import utilities


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
            (tuple):
                * BattleInfo: metadata about the match
                * tuple(tuple(Moveset)): the movesets used in the battle,
                    grouped by team
                * list(Matchup): list of matchups

        Raises:
            ParsingException: if there's a problem parsing the log

        """
        pass


class JsonFileLogReader(LogReader):

    def __init__(self, sanitizer=None, pokedex=None):
        """
        Parses Pokemon Showdown ``.json`` files

        Args:
            sanitizer (Optional(Sanitizer)):
                Used to normalize the data read in from the log. If none is
                    specified, will create its own
            pokedex (Optional(dict)):
                Used to calculate base stats. If none is specified will attempt
                to load from file, and if the file doesn't exist will scrape it
                from the Pokemon Showdown github
        """
        if sanitizer is None:
            sanitizer = utilities.Sanitizer()
        if pokedex is None:
            try:
                pokedex = json.load(open('resources/pokedex.json'))
            except IOError:
                pokedex = scrapers.scrape_battle_pokedex()

        self.sanitizer = sanitizer
        self.base_stats = dict()
        for pokemon in pokedex.keys():
            self.base_stats[pokemon] = utilities.stats_dict_to_dto(
                pokedex[pokemon]['baseStats'])

    def parse_log(self, log):
        """
        Parse the provided log and return structured data

        Args:
            log (str): file name of the battle log to parse

        Returns:
            (tuple):
                * BattleInfo: metadata about the match
                * tuple(tuple(Moveset)): the movesets used in the battle,
                    grouped by team
                * list(Matchup): list of matchups

        Raises:
            ParsingException: if there's a problem parsing the log
            FileNotFoundError: if the log doesn't exist
            json.decoder.JSONDecodeError: if the log is not a valid log

        """

        log = json.load(open(log))
        pass



