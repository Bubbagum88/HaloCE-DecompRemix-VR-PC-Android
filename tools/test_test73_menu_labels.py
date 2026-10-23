"""Test73: every settings screen's rows read their own labels. Found in the OpenCE 244 merge: Server Setup > Co-op
Options' VR INTERACTIONS and HOST VR ACTIONS still named labels 5 and 6 after 244's two new rows moved them to 7 and
8, so they would have read PER PLAYER: and PLAYER COLLISIONS:. For each column list of each menu file (port/assets/
menus/ce), per platform (a row's variants for different platforms may share a label): no two rows show the same
string of the same list, every label's index is inside its list, and where the screen's help is the label's
(menu_functions.c settings_help: the help list's [label index + 1]) the help list has a line for it."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CE = ROOT / 'port/assets/menus/ce'
PLATFORMS = ('desktop', 'android', 'web')

checked = 0
for path in sorted(CE.glob('*.xml')):
    root = ET.parse(path).getroot()
    widgets = {w.get('name'): w for w in root.iter('widget')}
    lists = {s.get('name'): s for s in root.iter('strings')}
    for menu in widgets.values():
        if menu.get('type') != 'column_list':
            continue
        help_widget = widgets.get(menu.get('description') or '')
        help_list = lists.get(help_widget.get('string_list')) if help_widget is not None else None
        per_label_help = any(d.get('input') == 'port settings help' for d in menu.findall('data'))
        seen = {}
        for child in menu.findall('child'):
            row = widgets.get(child.get('widget'))
            if row is None:
                continue
            platform = child.get('platform') or row.get('platform')
            shown = platform.split() if platform else list(PLATFORMS)
            stack, labels = [row], []
            while stack:
                widget = stack.pop()
                if widget.get('type') == 'text' and widget.get('name', '').endswith('_label') and \
                        widget.get('string_list') and widget.get('string_index'):
                    labels.append((widget.get('string_list'), int(widget.get('string_index'))))
                stack += [widgets[c.get('widget')] for c in widget.findall('child') if c.get('widget') in widgets]
            for label in labels:
                strings = lists.get(label[0])
                if strings is not None:
                    assert label[1] < len(strings.findall('string')), (path.name, row.get('name'), label)
                    if per_label_help and help_list is not None and help_list.get('name').endswith('help_strings'):
                        assert label[1] + 1 < len(help_list.findall('string')), (path.name, row.get('name'), label)
                for platform_name in shown:
                    other = seen.get((label, platform_name))
                    assert other is None or other == row.get('name'), \
                        '%s: %s and %s both show %s[%d] (%s)' % (path.name, other.rsplit('/', 1)[-1],
                                                                 row.get('name').rsplit('/', 1)[-1],
                                                                 label[0].rsplit('/', 1)[-1], label[1], platform_name)
                    seen[(label, platform_name)] = row.get('name')
                checked += 1
print('PASS: %d row labels: no two rows of a screen show one label on a platform; every index inside its list and '
      'its help' % checked)
