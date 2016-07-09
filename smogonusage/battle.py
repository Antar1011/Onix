"""Classes for structuring battle logs"""

import abc
import collections
import copy

from smogonusage.dto import Moveset, PokeStats


def _update_battle_state(initial_battle_state, events):
    """

    Args:
        initial_battle_state (BattleState) :
        events (:obj:`iterable` of :obj:`Event`) :

    Returns:
        BattleState : the updated battle state

    Raises:
        ValueError : if an effect in an event is inconsistent with the current
            battle state

    """
    battle_state = initial_battle_state.copy()

    return battle_state

Slot_ = collections.namedtuple("Slot", ['side', 'index'])
HPctChange_ = collections.namedtuple("HPctChange", ['slot', 'old_pct',
                                                    'new_pct'])
ConditionChange_ = collections.namedtuple("ConditionChange", ['slot',
                                                              'condition',
                                                              'recovery'])
StageChange_ = collections.namedtuple("StageChange", ['slot', 'stat',
                                                      'old_stage',
                                                      'new_stage'])
FieldChange_ = collections.namedtuple("FieldChange", ['side', 'field_condition',
                                                      'ending'])
MovesetChange_ = collections.namedtuple("MovesetChange", ['slot',
                                                          'old_moveset',
                                                          'new_moveset'])


class Slot(Slot_):
    """
    A reliable way to reference a Pokemon in a battle.

    Args:
        side (1 or 2) : the player number
        index (int) : the index of the Pokemon on the player's team
    """
    pass


class BattleState(object):
    """
    The state of the battle

    Args:
        teams: 
        leads: 
    """

    def __init__(self, teams, leads):
        
        self.teams = []
        for movesets in teams:
            team = []
            for moveset in movesets:
                team.append({'moveset': moveset,
                             'hpct': 100.0,
                             'nonvolatile_condition': None,
                             'volatile_condition': set(),
                             'stages': PokeStats(0, 0, 0, 0, 0, 0)})
            self.teams.append(team)
        self.active = leads
        self.field_conditions = [set() for _ in range(3)]

    def copy(self):
        return copy.deepcopy(self)


class Effect(object):
    """
    A change in the conditions of the battle. Could be damage infliction, could
    be a condition change (volatile, like confusion, or non-volatile, like burn
    or faint), or could be a change to the field (e.g. weather). Could be caused
    by a move, an item, an ability or a field effect (e.g. entry hazards)
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def apply_effect(self, battle_state, inplace=True):
        """
        Apply the effect to a battle state

        Args:
            battle_state (BattleState) : the battle state to which to apply
                the effect
            inplace (:obj:`bool`, optional) : if ``False``, makes a copy of the
                battle state before applying the effect, if ``True``, operate
                in-place. Default is ``True``.

        Returns:
            BattleState : the updated battle state
            
        Raises:
            ValueError : if the effect is inconsistent with the current battle
                state
        """


class HPctChange(HPctChange_, Effect):
    """
    A change in hit points, represented as percent health (exact, not rounded)

    Args:
        slot (Slot) : the slot of the affected Pokemon
        old_pct (float) : 100 * pre-event hit points / max hit points
        new_pct (float) : 100 * post-event hit points / max hit points
    """
    
    def apply_effect(self, battle_state, inplace=True):
        """
        Apply the HP change

        Args:
            battle_state (BattleState) : the battle state to which to apply
                the effect
            inplace (:obj:`bool`, optional) : if ``False``, makes a copy of the
                battle state before applying the effect, if ``True``, operate
                in-place. Default is ``True``.

        Returns:
            BattleState : the updated battle state

        Raises:
            ValueError : if the old HP of the specified Pokemon isn't what is
                expected by the effect.
        """

        if inplace is False:
            battle_state = battle_state.copy()

        slot = battle_state.teams[self.slot.side - 1][self.slot.index]
        
        # sanity check
        if slot['hpct'] != self.old_pct:
            raise ValueError("The Pokemon's current HP is inconsistent with the"
                             " expected HP for this effect.\n"
                             "Pokemon's current state:\n{0}\n"
                             "Expected hpct: {1}".format(slot, self.old_pct))
        
        slot['hpct'] = self.new_pct

        return battle_state


class VolatileConditionChange(ConditionChange_, Effect):
    """
    A change in volatile condition (e.g. confusion).

    Args:
        slot (Slot) : the slot of the affected Pokemon
        condition (str) : the condition
        recovery (bool) : ``False`` if this is a new condition (the Pokemon was
            previously unafflicted), ``True`` if the Pokemon is recovering from
            this condition
    """

    def apply_effect(self, battle_state, inplace=True):
        """
        Apply the volatile condition change

        Args:
            battle_state (BattleState) : the battle state to which to apply
                the effect
            inplace (:obj:`bool`, optional) : if ``False``, makes a copy of the
                battle state before applying the effect, if ``True``, operate
                in-place. Default is ``True``.

        Returns:
            BattleState : the updated battle state

        Raises:
            ValueError : if you're trying to cure the Pokemon of a condition it
                doesn't have or inflict it with a condition it already has
        """

        if inplace is False:
            battle_state = battle_state.copy()

        slot = battle_state.teams[self.slot.side - 1][self.slot.index]

        # sanity check
        has_condition = self.condition in slot['volatile_condition']
        if has_condition != self.recovery:
            raise ValueError("The Pokemon's current volatile condition is "
                             "inconsistent with the expected condition for this"
                             " effect.\n"
                             "Pokemon's current state:\n{0}\n"
                             "Expected to have {1} condition: {2}"
                             .format(slot, self.condition, self.recovery))

        if self.recovery:
            slot['volatile_condition'].remove(self.condition)
        else:
            slot['volatile_condition'].add(self.condition)

        return battle_state
    

class NonVolatileConditionChange(ConditionChange_, Effect):
    """
    A change in non-volatile (e.g. burn or faint).

    Args:
        slot (Slot) : the slot of the affected Pokemon
        condition (str) : the condition
        recovery (bool) : ``False`` if this is a new condition (the Pokemon was
            previously unafflicted), ``True`` if the Pokemon is recovering from
            this condition
    """

    def apply_effect(self, battle_state, inplace=True):
        """
        Apply the non-volatile condition change

        Args:
            battle_state (BattleState) : the battle state to which to apply
                the effect
            inplace (:obj:`bool`, optional) : if ``False``, makes a copy of the
                battle state before applying the effect, if ``True``, operate
                in-place. Default is ``True``.

        Returns:
            BattleState : the updated battle state

        Raises:
            ValueError : if ``self.condition`` is "faint" and ``self.recovery``
                is True (there's no reviving)
            ValueError : if you're trying to cure the Pokemon of a condition it
                doesn't have or inflict it with a condition (besides faint) when
                it already has a condition
        """

        if self.condition == 'faint' and self.recovery is True:
            raise ValueError("Pokemon cannot be revived.")
        if inplace is False:
            battle_state = battle_state.copy()

        slot = battle_state.teams[self.slot.side - 1][self.slot.index]

        # sanity check
        if self.recovery is False:
            expected_condition = None
        else:
            expected_condition = self.condition

        if expected_condition != slot['nonvolatile_condition'] and \
                        self.condition is not "faint":
            raise ValueError("The Pokemon's current non-volatile condition is "
                             "inconsistent with the expected condition for this"
                             " effect.\n"
                             "Pokemon's current state:\n{0}\n"
                             "Expected condition: {1}."
                             .format(slot, expected_condition))

        if self.recovery:
            slot['nonvolatile_condition'] = None
        else:
            slot['nonvolatile_condition'] = self.condition

        return battle_state


class StageChange(StageChange_, Effect):
    """
    A change in a stat's stage (e.g. -1 Atk due to Intimidate)

    Args:
        slot (Slot) : the slot of the affected Pokemon
        stat (str) : the affected stat
        old_stage (int) : the pre-event stage (0 is normal)
        new_stage (int) : the post-event stage (0 is normal)
    """

    def apply_effect(self, battle_state, inplace=True):
        """
        Apply the stage change

        Args:
            battle_state (BattleState) : the battle state to which to apply
                the effect
            inplace (:obj:`bool`, optional) : if ``False``, makes a copy of the
                battle state before applying the effect, if ``True``, operate
                in-place. Default is ``True``.

        Returns:
            BattleState : the updated battle state

        Raises:
            ValueError : if ``self.stat`` is "hp" (there are no HP stages)
            ValueError : if the old stage of the specified Pokemon isn't what is
                specified by the effect.
        """

        if self.stat == 'hp':
            raise ValueError("HP doesn't have stages")

        if inplace is False:
            battle_state = battle_state.copy()

        slot = battle_state.teams[self.slot.side - 1][self.slot.index]

        # sanity check
        if slot['stages']._asdict()[self.stat] != self.old_stage:
            raise ValueError("The Pokemon's current {0} stage is inconsistent "
                             "with the expected stage for this effect.\n"
                             "Pokemon's current state:\n{1}\n"
                             "Expected {0} stage: {2}".format(self.stat, slot,
                                                              self.old_stage))

        slot['stages'] = slot['stages']._replace(**{self.stat: self.new_stage})

        return battle_state


class FieldChange(FieldChange_, Effect):
    """
    A change in a field conditions (e.g. weather)

    Args:
        side (1, 2 or None) : the side affected (``None`` corresponds to both
            sides)
        field_condition (str) : the field condition
        ending (bool) : ``False`` if the field condition is starting, ``True``
            if the field effect is ending

    Note:
        Stacking entry hazards should be handled as the previous level ending
        and the next level beginning, e.g., laying down a second layer of
        spikes would be represented by
        ``[FieldChange(1, 'spikes_1', True),
        FieldChange(1, 'spikes_2', False)]``
    """

    def apply_effect(self, battle_state, inplace=True):
        """
        Apply the field condition change

        Args:
            battle_state (BattleState) : the battle state to which to apply
                the effect
            inplace (:obj:`bool`, optional) : if ``False``, makes a copy of the
                battle state before applying the effect, if ``True``, operate
                in-place. Default is ``True``.

        Returns:
            BattleState : the updated battle state

        Raises:
            ValueError : if you're trying to end a field condition that's not
                currently active or start one that's already active
        """

        if inplace is False:
            battle_state = battle_state.copy()
            
        side = self.side
        if side is None:
            side = 0

        field_conditions = battle_state.field_conditions[side]

        # sanity check
        has_condition = self.field_condition in field_conditions
        if has_condition != self.ending:
            raise ValueError("The current field conditions are "
                             "inconsistent with the expected conditions for "
                             "this effect.\n"
                             "Current conditions:\n{0}\n"
                             "Expected to have {1} condition: {2}"
                             .format(field_conditions, self.field_condition,
                                     self.ending))

        if self.ending:
            field_conditions.remove(self.field_condition)
        else:
            field_conditions.add(self.field_condition)

        return battle_state


class MovesetChange(MovesetChange_, Effect):
    """
    A change in an attribute of a Pokemon that's considered part of its Moveset
    (e.g. item, ability, stats...). This includes mega evolution and other forme
    changes.

    Note:
        The way to handle volatile changes (e.g. ability suppression or stat
        changes due to, say, Power Swap) is to revert the change on switch-out.

    Args:
        slot (Slot) : the slot of the affected Pokemon
        old_moveset (Moveset) : the pre-event moveset
        new_moveset (Moveset) : the post-event moveset
    """

    def apply_effect(self, battle_state, inplace=True):
        """
        Apply the non-volatile condition change

        Args:
            battle_state (BattleState) : the battle state to which to apply
                the effect
            inplace (:obj:`bool`, optional) : if ``False``, makes a copy of the
                battle state before applying the effect, if ``True``, operate
                in-place. Default is ``True``.

        Returns:
            BattleState : the updated battle state

        Raises:
            ValueError : if the old moveset of the specified Pokemon isn't what
                is expected by the effect.
        """

        if inplace is False:
            battle_state = battle_state.copy()

        slot = battle_state.teams[self.slot.side - 1][self.slot.index]

        # sanity check
        if self.old_moveset != slot['moveset']:
            raise ValueError("The Pokemon's current moveset is inconsistent "
                             "with the expected moveset for this effect.\n"
                             "Pokemon's current state:\n{0}\n"
                             "Expected moveset: {1}."
                             .format(slot, self.old_moveset))

        slot['moveset'] = self.new_moveset

        return battle_state


class Event(object):
    """
    Something that happened in a battle, e.g., a move or an ability being
    triggered
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_cause(self):
        """
        Get the cause of the event (e.g. the move or the field effect)

        Returns:
            object : the cause of the event
        """

    @abc.abstractmethod
    def get_effects(self):
        """
        Get the effects of the event (e.g. the damage dealt)
        
        Returns:
            :obj:`iterable` of `Effect` : the effects of the event

        """


class Move(object):
    """
    A move used by a Pokemon in a battle

    Args:
        move (str) : the name of the move
        user (Slot) : the slot of the Pokemon who used the move
        targets (:obj:`iterable` of :obj:`Slot`) : the slots of the Pokemon
            targeted by the move
        effects (:obj:`iterable` of :obj:`Effect`) : the effects of the move
        failure_reason (:obj:`str`, optional) : if the move failed, specify the
            reason why. If no reason is given, the move will be considered to
            have succeeded. Defaults to None (that is, to the move being
            successful)
    Attributes:
        move (str) : the name of the move
        user (Slot) : the slot of the Pokemon who used the move
        targets (:obj:`list` of :obj:`Slot`) : the slots of the Pokemon
            targeted by the move
        effects (:obj:`list` of :obj:`Effect`) : the effects of the move
        success (bool) : did the move succeed?
        failure_reason (str) : the reason why the move failed (if the move
            succeeded, then this will be None)
        """

    def __init__(self, move, user, targets, effects, failure_reason=None):

        self.move = move
        self.user = user
        self.targets = list(targets)
        self.effects = list(effects)
        if failure_reason is None:
            self.success = True
        else:
            self.success = False
        self.failure_reason = failure_reason
