"""Interfaces for storing data"""
import abc

from future.utils import with_metaclass


class _Sink(with_metaclass(abc.ABCMeta, object)):
    """Generic interface specifying methods that all sinks must implement"""

    @abc.abstractmethod
    def flush(self):
        """
        Flush any buffered operations

        Returns:
            None
        """

    @abc.abstractmethod
    def close(self):
        """
        Close the sink, flushing any buffered operations and releasing any
        locks on the underlying backend

        Returns:
            None
        """


class MovesetSink(_Sink):
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
            None
        """


class BattleInfoSink(_Sink):
    """Sink for storing battle metadata"""

    @abc.abstractmethod
    def store_battle_info(self, battle_info):
        """
        Store the provided battle info.

        Args:
            battle_info (onix.dto.BattleInfo) :
                The battle metadata to store

        Returns:
            None
        """


class BattleSink(_Sink):
    """Sink for storing the turn-by-turn battle logs"""

    @abc.abstractmethod
    def store_battle(self, battle):
        """
        Store the provided battle.

        Args:
            battle (onix.battle.Battle) :
                The battle to store

        Returns:
           None
        """
