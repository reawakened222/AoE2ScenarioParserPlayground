from AoE2ScenarioParser.objects.data_objects.condition import Condition
from AoE2ScenarioParser.objects.data_objects.effect import Effect
from AoE2ScenarioParser.objects.data_objects.trigger import Trigger
from AoE2ScenarioParser.objects.managers.de.trigger_manager_de import TriggerManagerDE
from AoE2ScenarioParser.scenarios.aoe2_scenario import AoE2Scenario
from AoE2ScenarioParser.datasets.players import PlayerId, PlayerColorId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.heroes import HeroInfo
from AoE2ScenarioParser.datasets.effects import EffectId
from typing import List, Dict

# The path to your scenario folder
input_folder = "./Stable_Baseline/"


def copy_triggers_from_p1(_trigger_manager, triggers, to_players: List[PlayerId]):
    def should_shift_variable(effect_type):
        correct_effect_type = effect_type in [EffectId.CHANGE_VARIABLE,
                                              EffectId.MODIFY_RESOURCE_BY_VARIABLE,
                                              EffectId.MODIFY_ATTRIBUTE_BY_VARIABLE]
        return correct_effect_type
    def should_shift_trigger_activation(effect: Effect):
        correct_trigger_effect = effect.effect_type in [EffectId.ACTIVATE_TRIGGER, EffectId.DEACTIVATE_TRIGGER]
        return correct_trigger_effect

    post_trigger_generation_update_effect_list = []
    for t in triggers:
        added_trigger_set = _trigger_manager.copy_trigger_per_player(from_player=PlayerId.ONE,
                                                                     trigger_select=t.trigger_id,
                                                                     include_player_source=True,
                                                                     create_copy_for_players=to_players)

        for Pid, trig in added_trigger_set.items():
            for area_cond in trig.conditions:
                pass
            for eff in trig.effects:
                if should_shift_variable(eff.effect_type):
                    if "Income" in _trigger_manager.get_variable(variable_id=eff.variable).name:
                        eff.variable = (int(Pid) - int(PlayerId.ONE)) * 3 + eff.variable % 3
                if should_shift_trigger_activation(eff):
                    _target_trigger_name = _trigger_manager.get_trigger(eff.trigger_id).name
                    if "Tick" in _target_trigger_name:
                        # For now, we add current player and effect pair to a list
                        src_trig_name = trig.name
                        post_trigger_generation_update_effect_list.append((Pid, src_trig_name, eff))

    for Pid, trig_name, eff in post_trigger_generation_update_effect_list:
        _new_trigger_name = None
        for res in ["Stone/", "Wood/", "Gold/"]:
            if res in trig_name:
                # For resources, there are several purchase triggers
                # They list the gain first - that part needs to be removed
                _new_trigger_name = f"{trig_name[trig_name.index(res):].replace('Buy', 'Tick')}"
                break
        if _new_trigger_name is None:
            _new_trigger_name = f"{trig_name.replace('Buy', 'Tick')}"


        # TODO: FIND A BETTER WAY TO SEARCH TRIGGER BY NAME!!!
        name_matching_triggers = [t for t in _trigger_manager.triggers if t.name == _new_trigger_name]
        assert len(name_matching_triggers) == 1
        eff.trigger_id = name_matching_triggers[0].trigger_id

# The scenario object.
scenario = AoE2Scenario.from_file(input_folder + "++BM++ --TD-- v4_1.aoe2scenario", game_version="DE")
trigger_manager = scenario.trigger_manager

# Adding this to remove the warning of about add_variable not existing in PyCharm
assert isinstance(trigger_manager, TriggerManagerDE)
for i in range(2, 8):
    # This needs to be in same order as the hardcoded variables in the map!
    trigger_manager.add_variable(f"P{i}_Stone_Periodic_Income")
    trigger_manager.add_variable(f"P{i}_Gold_Periodic_Income")
    trigger_manager.add_variable(f"P{i}_Wood_Periodic_Income")

player_one_triggers = [t for t in trigger_manager.triggers if "P1" in str.upper(t.name)]
all_human_players = [PlayerId.TWO, PlayerId.THREE]
copy_triggers_from_p1(trigger_manager, player_one_triggers, all_human_players)

scenario.write_to_file("./.output/" + "output_test.aoe2scenario")
