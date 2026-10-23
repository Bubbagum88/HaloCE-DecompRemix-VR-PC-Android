"""The scenery and devices whose damage every machine shares: a body to destroy, or a shield to break."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from harness import CHECK_FAILED, build, function, mutated, read, run


def generated(fault=None):
    source = read('port/linux/game/network_damage.c')
    # (HaloCE-Quest-VR: and this port's gate for a client of a host before 34, static_target_shields)
    code = '\n'.join(function(source, name) for name in ('static_target_shields', 'static_target',
                                                         'static_target_damage', 'distributed_distance_squared',
                                                         'static_target_near'))
    if fault:
        code = mutated(code, *fault)
    return (('under_test.inc', code),)


@pytest.mark.parametrize('case', ['body', 'shield', 'neither', 'damage', 'near', 'old-host'])  # HaloCE-Quest-VR: old-host
def test_case(case):
    status, output = run(build('static_target', generated()), case)
    assert status == 0, output


@pytest.mark.parametrize('fault,case', [
    # (the shield-only objects left out, as before: Rat Race's shields, a map's tripmines)
    # (HaloCE-Quest-VR: on this port's line, which has the gate for hosts before 34)
    (('||\n\t\t\t(static_target_shields() && object_get_maximum_shield_vitality(object_index, TRUE) > 0.0f)', ''),
     'shield'),
    # (HaloCE-Quest-VR: the gate gone, a client of a host before 34 takes 34's static targets)
    (('return game_connection() != _game_connection_network_client || network_game_client_joined_version() >= 34;',
      'return TRUE;'), 'old-host'),
    (('STATIC_TARGET_TYPES)', 'STATIC_TARGET_TYPES | _object_mask_unit)'), 'neither'),
    (('object_get_maximum_body_vitality(object_index, TRUE) > 0.0f ||', ''), 'body'),
    (('damage->owner_object_index != NONE && static_target(damage->owner_object_index)', 'FALSE'), 'damage'),
    (('distance < nearest_distance', 'distance > nearest_distance'), 'near'),
    (('if (!static_target(iterator.index))\n\t\t\tcontinue;', ''), 'near'),
])
def test_negative_control(fault, case):
    status, output = run(build('static_target', generated(fault)), case)
    assert status == CHECK_FAILED, output
