"""Interfaces for storing data"""
import abc

from future.utils import with_metaclass


class MovesetSink(with_metaclass(abc.ABCMeta, object)):
    """Sink for storing movesets"""

    @abc.abstractmethod
    def store_movesets(self, movesets):
        """
        Store the provided movesets.

        Args:
            movesets (:obj:`dict` of :obj:`str` to :obj:`onix.dto.Moveset`) :
                A map where the values are the movesets to store and the keys
                their corresponding set IDs.

        Returns:
            int :
                The number of movesets stored as a result of this operation
        """


class BattleInfoSink(with_metaclass(abc.ABCMeta, object)):
    """Sink for storing battle metadata"""

    @abc.abstractmethod
    def store_battle_info(self, battle_info):
        """
        Store the provided battle info.

        Args:
            battle_info (onix.dto.BattleInfo) :
                The battle metadata to store

        Returns:
            :obj:`dict` of :obj:`str` to :obj:`int` :
                The number of new objects stored as a result of this operation,
                grouped by type (the keys in this dictionary may vary from
                implementation to implementation)
        """


class BattleSink(with_metaclass(abc.ABCMeta, object)):
    """Sink for storing the turn-by-turn battle logs"""

    @abc.abstractmethod
    def store_battle(self, battle):
        """
        Store the provided battle.

        Args:
            battle (onix.battle.Battle) :
                The battle to store

        Returns:
            bool :
                True if the battle was successfully stored, False otherwise
        """
