"""Test73, item 11: the licence after OpenCE's change to the AGPL 3.0 or later (its 4b09168e7, merged with Builds 242 to
246). The tree's LICENSE is the AGPL text and LICENSES/CC0-1.0.txt the CC0 dedication of the code from before the
change; LICENSE.md and extract-xiso (whose readers OpenCE wrote again) are gone, and everything that names or ships
them says so: THIRD-PARTY-NOTICES.txt (the AGPL text first, then CC0; no extract-xiso), CREDITS.md, README.md's
Licence section, CONTRIBUTING.md, the package script's notices (LICENSE.txt and CC0-1.0.txt in the build zip, as
tools/ci_build.py ships them) and the APK's credits page (credits.txt carries the notices, the AGPL text with them)."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    text = (ROOT / rel).read_text(encoding='utf-8')
    assert '\r' not in text, rel
    return text


agpl = read('LICENSE')
cc0 = read('LICENSES/CC0-1.0.txt')
assert agpl.lstrip().startswith('GNU AFFERO GENERAL PUBLIC LICENSE') and 'Version 3, 19 November 2007' in agpl
assert 'Remote Network Interaction; Use with the GNU General Public License' in agpl and agpl.count('\n') > 600
assert cc0.startswith('Creative Commons Legal Code') and 'CC0 1.0 Universal' in cc0
assert not (ROOT / 'LICENSE.md').exists() and not (ROOT / 'port/third_party/extract-xiso').exists()

notices = read('THIRD-PARTY-NOTICES.txt')
sections = re.findall(r'^===== (.+?) =====$', notices, re.M)
assert sections[:2] == ['LICENSE (GNU Affero General Public License 3.0)', 'LICENSES/CC0-1.0.txt'], sections[:3]
first = notices[notices.index('===== LICENSE (GNU'):notices.index('===== LICENSES/CC0-1.0.txt =====')]
second = notices[notices.index('===== LICENSES/CC0-1.0.txt ====='):notices.index('===== ' + sections[2] + ' =====')]
assert agpl.rstrip('\n') in first and cc0.rstrip('\n') in second
assert 'extract-xiso' not in notices and 'fishtank' not in notices and 'LICENSE.md' not in notices
assert 'GNU Affero General Public License\n3.0 or (at your option) any later version' in notices[:600]

credits = read('CREDITS.md')
assert 'LICENSE.md' not in credits and 'inherited CC0 dedication' not in credits
assert 'GNU Affero General Public License 3.0 or (at your option) any later version ([LICENSE](LICENSE))' in credits
assert '[LICENSES/CC0-1.0.txt](LICENSES/CC0-1.0.txt)' in credits and '4b09168e7' in credits
assert 'no\nextract-xiso code is included' in credits or 'no extract-xiso code is included' in credits.replace('\n', ' ')
assert '## Test73 additions' in credits and 'ringfall-mjolnir-vr' in credits and 'astromaddie' in credits

readme = read('README.md')
licence = readme[readme.index('## Licence'):]
assert '`AGPL-3.0-or-later`' in licence and '[LICENSE](LICENSE)' in licence and '[CC0 1.0](LICENSES/CC0-1.0.txt)' in licence
assert 'section 13' in licence and 'Halo is not covered' in licence
assert 'GNU AGPL 3.0 or later' in read('CONTRIBUTING.md') and 'Pillow at 12.0.0' in read('CONTRIBUTING.md')

package = read('tools/package-quest.py')
assert '"LICENSE.md"' not in package  # (no longer copied anywhere; a comment says why)
assert ('("LICENSE", "LICENSE.txt"), ("LICENSES/CC0-1.0.txt", "CC0-1.0.txt")]:' in package and
        'shutil.copy2(ROOT / notice, output / name)' in package)
ci = read('tools/ci_build.py')
assert 'shutil.copy2(ROOT / "LICENSE", dist / "LICENSE.txt")' in ci and 'shutil.copy2(ROOT / "LICENSES/CC0-1.0.txt", dist / "CC0-1.0.txt")' in ci
generator = read('tools/generate-field-guide.py')
assert "(OUT/'credits.txt').write_text((ROOT/'CREDITS.md').read_text(encoding='utf-8')+'\\n\\n'+(ROOT/'THIRD-PARTY-NOTICES.txt')" in generator
print('PASS: Test73 licence: LICENSE the AGPL 3.0 text and LICENSES/CC0-1.0.txt the earlier CC0, both first in the notices '
      '(no extract-xiso, no LICENSE.md), and CREDITS, README, CONTRIBUTING, the build zip and the APK\'s credits page say so')
