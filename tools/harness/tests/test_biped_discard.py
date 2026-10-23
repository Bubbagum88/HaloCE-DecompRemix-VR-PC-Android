"""A biped fallen out of the map, erased by whoever owns it: a client leaves the host's to the host."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from harness import CHECK_FAILED, build, enum_with, function, mutated, read, run

# HaloCE-Quest-VR: 'vr-held', a body the player holds in VR, is never erased
CASES = ['client', 'client-own', 'host', 'above', 'vr-held']


def generated(fault=None):
    config = enum_with(read('source/objects/objects.h'), '_object_outside_of_map_bit') + '\n'
    code = '\n'.join([
        'static long objects_client_has[MAXIMUM_TRACKED_OBJECTS];',
        'static boolean objects_client_deleting;',
        function(read('port/linux/game/network_objects.c'), 'network_objects_may_delete'),
        # HaloCE-Quest-VR: upstream's inline check is this port's biped_port_may_discard
        # (VR-held bodies kept; a client's one note for the host's biped)
        function(read('source/units/bipeds.c'), 'biped_port_may_discard'),
        function(read('source/units/bipeds.c'), 'biped_check_discard'),
    ])
    if fault:
        code = mutated(code, *fault)
    return (('config.inc', config), ('under_test.inc', code))


@pytest.mark.parametrize('case', CASES)
def test_case(case):
    status, output = run(build('biped_discard', generated()), case)
    assert status == 0, output


def test_negative_control():
    fault = (' &&\n\t\tbiped_port_may_discard(biped_index))', ')')  # HaloCE-Quest-VR: our line
    status, output = run(build('biped_discard', generated(fault)), 'client')
    assert status == CHECK_FAILED, output
