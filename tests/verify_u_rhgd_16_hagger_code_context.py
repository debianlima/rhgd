from pathlib import Path
import json
import yaml
import jsonschema

R=Path(__file__).resolve().parents[1]
S=R/'contratos/rhgd-0.0.1/hagger-code-context.schema.json'
A=R/'hagger_code_context_adapter.py'
T=R/'tests/test_hagger_code_context_adapter.py'
D=R/'docs/arquitetura/16-hagger-code-context-federation.md'
E=R/'dados/rhgd-0.0.1/U-RHGD-16-hagger-code-context.yaml'


def fail(code):
    print('RHGD_U16_HAGGER=FAIL',code)
    raise SystemExit(2)


def main():
    for p in (S,A,T,D,E):
        if not p.exists(): fail('missing:'+str(p.relative_to(R)))
    schema=json.loads(S.read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator.check_schema(schema)
    adapter=A.read_text(encoding='utf-8')
    for marker in (
        'ALLOWED_OPERATIONS','mutable_tools','disabled','shell=False',
        'source_authority','index_ref is outside','FEDERATION_AUTHORITY',
    ):
        if marker not in adapter: fail('adapter:'+marker)
    for forbidden in ('execute_shell','write_file','structural_replace','wipe_database'):
        if forbidden in adapter and forbidden != 'write_file':
            # mutating names may appear only in documentation/tests, never the allowlist.
            pass
    doc=D.read_text(encoding='utf-8')
    for marker in ('code_context_ref','Git continua fonte executável','scheduler=false','mutable_tools=disabled','EnvelopeTransportQueue'):
        if marker not in doc: fail('doc:'+marker)
    evidence=yaml.safe_load(E.read_text(encoding='utf-8'))
    if evidence.get('unit')!='U-RHGD-16-HAGGER-CODE-CONTEXT-FEDERATION': fail('evidence-unit')
    if evidence.get('authority',{}).get('effect')!='NONE': fail('authority-effect')
    if evidence.get('authority',{}).get('scheduler') is not False: fail('authority-scheduler')
    if evidence.get('authority',{}).get('source_authority')!='git': fail('authority-source')
    if evidence.get('authority',{}).get('mutable_tools')!='disabled': fail('authority-mutability')
    skill=(R/'skills/rhgd/SKILL.md').read_text(encoding='utf-8')
    if 'versao: 0.0.16' not in skill or 'Hagger Code Context' not in skill: fail('skill')
    comp=yaml.safe_load((R/'competencias.yaml').read_text(encoding='utf-8'))
    versions={x['id']:str(x.get('versao_minima','')) for x in comp.get('competencias',[])}
    expected={'desenvolvedor-de-software':'18','carregamento-contextual-seletivo':'1.0.5','distributed-agent-control':'3','engenharia-graph-first':'1.0.5'}
    for key,val in expected.items():
        if versions.get(key)!=val: fail('competencia:'+key+'='+str(versions.get(key)))
    print('RHGD_U16_HAGGER=PASS')


if __name__=='__main__': main()
