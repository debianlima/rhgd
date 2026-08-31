from pathlib import Path
import re, sys
root=Path(__file__).resolve().parents[1]
required=['README.md','VERSION','manifesto.yaml','competencias.yaml','estado.md','lexico.yaml','skills/rhgd/SKILL.md']
missing=[p for p in required if not (root/p).exists()]
text=(root/'manifesto.yaml').read_text(encoding='utf-8')
paths=re.findall(r'caminho:\s*([^,}\n]+)',text)
undeclared=[p.strip() for p in paths if not (root/p.strip()).exists()]
skills=list(root.glob('skills/*/SKILL.md'))
assert not missing, f'missing={missing}'
assert not undeclared, f'manifest_missing={undeclared}'
assert len(skills)==1, f'project_skills={skills}'
assert (root/'VERSION').read_text().strip()=='0.0.1'
print('RHGD_PROJECT_VERIFY=PASS')
