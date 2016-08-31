"""Functionality for processing of logs and routing parsed data to sinks"""
import glob

from onix import contexts
from onix.collection import log_reader
from onix.collection import sinks


class LogProcessor(object):
    """
    Executor in charge of processing battle logs and routing the parsed data to
    the appropriate sinks

    Args:
        moveset_sink (sinks.MovesetSink) : The sink to route movesets data
        battle_info_sink (sinks.BattleInfoSink) :
            The sink to route battle metadata
        battle_sink (sinks.BattleSink) :
            The sink to route the actual turn-by-turn battle representations
        context (onix.contexts.Context) :
            The resources needed by the log reader. Must have: pokedex, items,
            formats, sanitizer, accessible_formes and natures
    """

    def __init__(self, moveset_sink, battle_info_sink, battle_sink, context):
        contexts.require(context, 'sanitizer', 'pokedex', 'items', 'formats',
                         'natures', 'accessible_formes')
        self.moveset_sink = moveset_sink
        self.battle_info_sink = battle_info_sink
        self.battle_sink = battle_sink
        self.context = context
        self.readers = {}

    def process_logs(self, logs, ref_type='folder'):
        """
        Process the specified logs

        Args:
            logs : Reference to the logs to process
            ref_type (:obj:`str`, optional) :
                Description of the `logs` parameter specifying how to handle it.
                Options are:
                    * "file" : specifying a single JSON log
                    * "files" : specifying an iterable of JSON logs
                    * "folder" : specifying a directory or nested directory of
                        JSON logs
                Defaults to "folder"

        Returns:
            int :
                the number of logs processed successfully
        """
