"""Functionality for processing of logs and routing parsed data to sinks"""
import glob

from onix import contexts
from onix.collection import log_reader
from onix.collection import sinks


class LogProcessor(object):
    """
    Executor in charge of processing battle logs and routing the parsed data to
    the appropriate sinks. The LogProcessor is in charge of instantiating
    ``LogReader``s to process the logs that come in based on the format of the
    log (_e.g._ JSON file) and the metagame of the battle.

    Args:
        moveset_sink (sinks.MovesetSink) : The sink to route movesets data
        battle_info_sink (sinks.BattleInfoSink) :
            The sink to route battle metadata
        battle_sink (sinks.BattleSink) :
            The sink to route the actual turn-by-turn battle representations
        force_context_refresh (:obj:`bool`, optional) : Defaults to False. If
            True, any contexts that get loaded will be pull fresh data from
            Pokemon Showdown rather than rely on the local cache.
    """

    def __init__(self, moveset_sink, battle_info_sink, battle_sink,
                 force_context_refresh=False):

        self.moveset_sink = moveset_sink
        self.battle_info_sink = battle_info_sink
        self.battle_sink = battle_sink
        self.readers = {}

    def process_logs(self, logs, ref_type='folder', **kwargs):
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
            **kwargs :
                Additional keyword arguments specific to the ref_type.
                    * "file" and "files" require:
                        * date (:obj:`datetime.datetime`) :
                            the date on which the battle took place
                        * format (:obj:`str`) : sanitized name of the metagame

        Returns:
            int :
                the number of logs processed successfully
        """
