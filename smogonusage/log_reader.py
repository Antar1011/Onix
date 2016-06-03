"""Functionality for taking PS logs & structuring them into a desired format"""

import abc

from smogonusage.moveset import Moveset


class LogReader(object):
    """
    An object which takes in a Pokemon Showdown log (in whatever format it
    exists) and returned structured data, ready for compiling or storing
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def parse_log(self, log):
        """
        Parse the provided log and return structured
        Args:
            log: log of the  battle, in whatever format the reader can parse

        Returns:
            BattleInfo: metadata about the match
            tuple(tuple(Moveset)): the movesets used in the battle, grouped by
                team
            list(Matchup): list of matchups

        Raises:
            ParsingException: if there's a problem parsing the log

        """
        pass
