"""Tests for the battle.py module"""
import pytest

from smogonusage import battle
from smogonusage.dto import Moveset, PokeStats


class TestHPctChange(object):

    def setup_method(self, method):
        moveset_1 = Moveset('gardevoir', 'synchronize', 'u', 'choicescarf',
                            ['healingwish'], PokeStats(340, 121, 251, 286, 266,
                                                       197), 100, 255)
        moveset_2 = Moveset('blastoisemega', 'megalauncher', 'f',
                            'blastoisinite', ['aurasphere', 'darkpulse',
                                              'dragonpulse', 'waterspout'],
                            PokeStats(361, 189, 276, 405, 268, 192), 100, 255)

        self.state = battle.BattleState([[moveset_1], [moveset_2]], [[0], [0]])

    def test_damage(self):
        effect = battle.HPctChange(battle.Slot(1, 0), 100.0, 40.0)
        updated_state = effect.apply_effect(self.state)

        assert 40.0 == updated_state.teams[0][0]['hpct']

    def test_healing(self):
        self.state.teams[0][0]['hpct'] = 40.0
        effect = battle.HPctChange(battle.Slot(1, 0), 40.0, 90.0)
        updated_state = effect.apply_effect(self.state)

        assert 90.0 == updated_state.teams[0][0]['hpct']

    def test_inconsistent(self):
        effect = battle.HPctChange(battle.Slot(1, 0), 40.0, 90.0)
        with pytest.raises(ValueError):
            effect.apply_effect(self.state)

    def test_inplace_by_default(self):
        effect = battle.HPctChange(battle.Slot(1, 0), 100.0, 40.0)
        effect.apply_effect(self.state)

        assert 40.0 == self.state.teams[0][0]['hpct']

    def test_copy(self):
        effect = battle.HPctChange(battle.Slot(1, 0), 100.0, 40.0)
        effect.apply_effect(self.state, inplace=False)

        assert 100.0 == self.state.teams[0][0]['hpct']


class TestVolatileConditionChange(object):

    def setup_method(self, method):
        moveset_1 = Moveset('gardevoir', 'synchronize', 'u', 'choicescarf',
                            ['healingwish'], PokeStats(340, 121, 251, 286, 266,
                                                       197), 100, 255)
        moveset_2 = Moveset('blastoisemega', 'megalauncher', 'f',
                            'blastoisinite', ['aurasphere', 'darkpulse',
                                              'dragonpulse', 'waterspout'],
                            PokeStats(361, 189, 276, 405, 268, 192), 100, 255)

        self.state = battle.BattleState([[moveset_1], [moveset_2]], [[0], [0]])

    def test_confuse(self):
        effect = battle.VolatileConditionChange(battle.Slot(1, 0), 'confusion',
                                                False)
        updated_state = effect.apply_effect(self.state)

        assert 'confusion' in updated_state.teams[0][0]['volatile_condition']

    def test_recover(self):
        self.state.teams[0][0]['volatile_condition'].add('confusion')
        effect = battle.VolatileConditionChange(battle.Slot(1, 0), 'confusion',
                                                True)
        updated_state = effect.apply_effect(self.state)

        assert 'confusion' not in updated_state.teams[0][0][
            'volatile_condition']

    def test_inconsistent(self):
        self.state.teams[0][0]['volatile_condition'].add('confusion')
        effect = battle.VolatileConditionChange(battle.Slot(1, 0), 'confusion',
                                                False)
        with pytest.raises(ValueError):
            effect.apply_effect(self.state)

    def test_inconsistent_recover(self):
        effect = battle.VolatileConditionChange(battle.Slot(1, 0), 'confusion',
                                                True)
        with pytest.raises(ValueError):
            effect.apply_effect(self.state)

    def test_inplace_by_default(self):
        effect = battle.VolatileConditionChange(battle.Slot(1, 0), 'confusion',
                                                False)
        effect.apply_effect(self.state)

        assert 'confusion' in self.state.teams[0][0]['volatile_condition']

    def test_copy(self):
        effect = battle.VolatileConditionChange(battle.Slot(1, 0), 'confusion',
                                                False)
        effect.apply_effect(self.state, inplace=False)

        assert 'confusion' not in self.state.teams[0][0]['volatile_condition']


class TestNonVolatileConditionChange(object):

    def setup_method(self, method):
        moveset_1 = Moveset('gardevoir', 'synchronize', 'u', 'choicescarf',
                            ['healingwish'], PokeStats(340, 121, 251, 286, 266,
                                                       197), 100, 255)
        moveset_2 = Moveset('blastoisemega', 'megalauncher', 'f',
                            'blastoisinite', ['aurasphere', 'darkpulse',
                                              'dragonpulse', 'waterspout'],
                            PokeStats(361, 189, 276, 405, 268, 192), 100, 255)

        self.state = battle.BattleState([[moveset_1], [moveset_2]], [[0], [0]])

    def test_burn(self):
        effect = battle.NonVolatileConditionChange(battle.Slot(1, 0), 'burn',
                                                   False)
        updated_state = effect.apply_effect(self.state)

        assert 'burn' == updated_state.teams[0][0]['nonvolatile_condition']

    def test_recover(self):
        self.state.teams[0][0]['nonvolatile_condition'] = 'burn'
        effect = battle.NonVolatileConditionChange(battle.Slot(1, 0), 'burn',
                                                   True)
        updated_state = effect.apply_effect(self.state)

        assert updated_state.teams[0][0]['nonvolatile_condition'] is None

    def test_inconsistent(self):
        self.state.teams[0][0]['nonvolatile_condition'] = 'burn'
        effect = battle.NonVolatileConditionChange(battle.Slot(1, 0), 'burn',
                                                   False)
        with pytest.raises(ValueError):
            effect.apply_effect(self.state)

    def test_inconsistent_recover(self):
        effect = battle.NonVolatileConditionChange(battle.Slot(1, 0), 'burn',
                                                   True)
        with pytest.raises(ValueError):
            effect.apply_effect(self.state)

    def test_inplace_by_default(self):
        effect = battle.NonVolatileConditionChange(battle.Slot(1, 0), 'burn',
                                                   False)
        effect.apply_effect(self.state)

        assert 'burn' == self.state.teams[0][0]['nonvolatile_condition']

    def test_copy(self):
        effect = battle.NonVolatileConditionChange(battle.Slot(1, 0), 'burn',
                                                   False)
        effect.apply_effect(self.state, inplace=False)

        assert self.state.teams[0][0]['nonvolatile_condition'] is None

    def test_faint_overrides_previous_status(self):
        self.state.teams[0][0]['nonvolatile_condition'] = 'burn'
        effect = battle.NonVolatileConditionChange(battle.Slot(1, 0), 'faint',
                                                   False)
        updated_state = effect.apply_effect(self.state)
        assert 'faint' == updated_state.teams[0][0]['nonvolatile_condition']

    def test_no_revive(self):
        self.state.teams[0][0]['nonvolatile_condition'] = 'faint'
        effect = battle.NonVolatileConditionChange(battle.Slot(1, 0), 'faint',
                                                   True)
        with pytest.raises(ValueError):
            effect.apply_effect(self.state)


class TestStageChange(object):

    def setup_method(self, method):
        moveset_1 = Moveset('gardevoir', 'synchronize', 'u', 'choicescarf',
                            ['healingwish'], PokeStats(340, 121, 251, 286, 266,
                                                       197), 100, 255)
        moveset_2 = Moveset('blastoisemega', 'megalauncher', 'f',
                            'blastoisinite', ['aurasphere', 'darkpulse',
                                              'dragonpulse', 'waterspout'],
                            PokeStats(361, 189, 276, 405, 268, 192), 100, 255)

        self.state = battle.BattleState([[moveset_1], [moveset_2]], [[0], [0]])

    def test_lower_attack(self):
        effect = battle.StageChange(battle.Slot(1, 0), 'atk', 0, -1)
        updated_state = effect.apply_effect(self.state)

        assert -1 == updated_state.teams[0][0]['stages'].atk

    def test_raise_speed(self):
        self.state.teams[0][0]['stages'] = PokeStats(0, 0, 0, 0, 0, 2)
        effect = battle.StageChange(battle.Slot(1, 0), 'spe', 2, 4)
        updated_state = effect.apply_effect(self.state)

        assert 4 == updated_state.teams[0][0]['stages'].spe

    def test_inconsistent(self):
        effect = battle.StageChange(battle.Slot(1, 0), 'atk', -1, -3)
        with pytest.raises(ValueError):
            effect.apply_effect(self.state)

    def test_no_hp_stage_change(self):
        effect = battle.StageChange(battle.Slot(1, 0), 'hp', 0, 1)
        with pytest.raises(ValueError):
            effect.apply_effect(self.state)

    def test_inplace_by_default(self):
        effect = battle.StageChange(battle.Slot(1, 0), 'atk', 0, -1)
        effect.apply_effect(self.state)

        assert -1 == self.state.teams[0][0]['stages'].atk

    def test_copy(self):
        effect = battle.StageChange(battle.Slot(1, 0), 'atk', 0, -1)
        effect.apply_effect(self.state, inplace=False)

        assert 0 == self.state.teams[0][0]['stages'].atk


class TestFieldChange(object):

    def setup_method(self, method):
        moveset_1 = Moveset('gardevoir', 'synchronize', 'u', 'choicescarf',
                            ['healingwish'], PokeStats(340, 121, 251, 286, 266,
                                                       197), 100, 255)
        moveset_2 = Moveset('blastoisemega', 'megalauncher', 'f',
                            'blastoisinite', ['aurasphere', 'darkpulse',
                                              'dragonpulse', 'waterspout'],
                            PokeStats(361, 189, 276, 405, 268, 192), 100, 255)

        self.state = battle.BattleState([[moveset_1], [moveset_2]], [[0], [0]])

    def test_weather(self):
        effect = battle.FieldChange(None, 'rain', False)

        updated_state = effect.apply_effect(self.state)

        assert 'rain' in updated_state.field_conditions[0]

    def test_weather_end(self):
        self.state.field_conditions[0].add('rain')
        effect = battle.FieldChange(None, 'rain', True)

        updated_state = effect.apply_effect(self.state)

        assert 'rain' not in updated_state.field_conditions[0]

    def test_entry_hazards(self):
        effect = battle.FieldChange(2, 'stickyweb', False)

        updated_state = effect.apply_effect(self.state)

        assert 'stickyweb' not in updated_state.field_conditions[2]

    def test_entry_hazards(self):
        effect = battle.FieldChange(2, 'stickyweb', False)

        updated_state = effect.apply_effect(self.state)

        assert 'stickyweb' in updated_state.field_conditions[2]

    def test_inconsistent_weather(self):
        self.state.field_conditions[0].add('sun')
        effect = battle.FieldChange(None, 'sun', False)
        with pytest.raises(ValueError):
            effect.apply_effect(self.state)

    def test_improper_hazard_stacking(self):
        self.state.field_conditions[1].add('toxic_spikes')
        effect = battle.FieldChange(1, 'toxic_spikes', False)
        with pytest.raises(ValueError):
            effect.apply_effect(self.state)

    def test_inplace_by_default(self):
        effect = battle.FieldChange(None, 'rain', False)
        effect.apply_effect(self.state)

        assert 'rain' in self.state.field_conditions[0]

    def test_copy(self):
        effect = battle.FieldChange(None, 'rain', False)
        effect.apply_effect(self.state, inplace=False)

        assert 'rain' not in self.state.field_conditions[0]


class TestMovesetChange(object):

    def setup_method(self, method):
        moveset_1 = Moveset('shayminsky', 'serenegrace', 'u', 'choicespecs',
                            ['airslash', 'seedflare', 'hiddenpowerice',
                             'earthpower'], PokeStats(341, 189, 185, 339, 187,
                                                       388), 100, 255)
        moveset_2 = Moveset('blastoise', 'raindish', 'f',
                            'blastoisinite', ['aurasphere', 'darkpulse',
                                              'dragonpulse', 'waterspout'],
                            PokeStats(361, 153, 236, 295, 248, 192), 100, 255)

        self.state = battle.BattleState([[moveset_1], [moveset_2]], [[0], [0]])

    def test_mega_evolve(self):
        effect = battle.HPctChange(battle.Slot(1, 0), 100.0, 40.0)
        updated_state = effect.apply_effect(self.state)

        assert 40.0 == updated_state.teams[0][0]['hpct']

    def test_healing(self):
        self.state.teams[0][0]['hpct'] = 40.0
        effect = battle.HPctChange(battle.Slot(1, 0), 40.0, 90.0)
        updated_state = effect.apply_effect(self.state)

        assert 90.0 == updated_state.teams[0][0]['hpct']

    def test_inconsistent(self):
        effect = battle.HPctChange(battle.Slot(1, 0), 40.0, 90.0)
        with pytest.raises(ValueError):
            effect.apply_effect(self.state)

    def test_inplace_by_default(self):
        effect = battle.HPctChange(battle.Slot(1, 0), 100.0, 40.0)
        effect.apply_effect(self.state)

        assert 40.0 == self.state.teams[0][0]['hpct']

    def test_copy(self):
        effect = battle.HPctChange(battle.Slot(1, 0), 100.0, 40.0)
        effect.apply_effect(self.state, inplace=False)

        assert 100.0 == self.state.teams[0][0]['hpct']

