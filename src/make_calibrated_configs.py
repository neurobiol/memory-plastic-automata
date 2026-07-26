from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sel = json.loads((ROOT / 'configs/calibrated_defaults.json').read_text())['selected_defaults']
out = ROOT / 'configs/generated'; out.mkdir(exist_ok=True)
for name in ['primary', 'secondary', 'sensitivity', 'ablation', 'sequential_exact']:
    src = ROOT / 'configs' / f'config_{name}.json'
    j = json.loads(src.read_text())
    j.setdefault('defaults', {}).update(sel)
    (out / f'config_{name}.json').write_text(json.dumps(j, indent=2))
print('CALIBRATED CONFIGS COMPLETED')
