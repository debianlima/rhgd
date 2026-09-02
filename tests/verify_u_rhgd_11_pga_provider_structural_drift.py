#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / 'contratos/rhgd-0.0.1/provider-contract-freshness.schema.json'
DATA = ROOT / 'dados/rhgd-0.0.1/U-RHGD-11-pga-provider-structural-drift.yaml'
DOC = ROOT / 'docs/arquitetura/11-pga-provider-structural-drift.md'
PGA_BEFORE = '5d1dfd93b0525db26b44efaea8bdbc56f25c185c'
PGA_AFTER = '871f0294deb0a595e7e1de49ae776dadc098f2c6'
CONSUMED = {
    'contratos/pga-1.0/network-service-agents.schema.json': '504df737545226ac6837fea6299d4ccd0732f9197bcdadf948f03886209a361a',
    'contratos/pga-1.0/deterministic-priority-policy.schema.json': '2d84c843b9d8f4debcea7efe58a44ec7b8d31d2dfabf1ed5eb393dffd9b71126',
    'dados/pga-1.0/U-PGA-08-network-service-agents.yaml': '6bfafab444b09c3f156e49d13550e463f1bc317c57dfea1d5f1e682e68ff39a8',
    'dados/pga-1.0/U-PGA-09-deterministic-priority-policy.yaml': '31b8ebd3e06ecd7729a076617fa6dfd9dc251fd41bf0e1ded26390c42d0f4881',
}
EXPECTED_CHANGED = {
    'dados/telemetria-unidades.jsonl',
    'estado.md',
    'manifesto.yaml',
    'tests/verify_project.py',
}
FORBIDDEN_PREFIXES = (
    'contratos/pga-1.0/network-service-agents.schema.json',
    'contratos/pga-1.0/deterministic-priority-policy.schema.json',
    'dados/pga-1.0/U-PGA-08-network-service-agents.yaml',
    'dados/pga-1.0/U-PGA-09-deterministic-priority-policy.yaml',
    'docs/U-PGA-08-network-service-agents.md',
    'docs/U-PGA-09-deterministic-priority-policy.md',
    'skills/pga/SKILL.md',
)


def fail(msg: str) -> None:
    print('RHGD_U11_PGA_PROVIDER_STRUCTURAL_DRIFT=FAIL', msg)
    raise SystemExit(2)


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def blob_sha(repo: Path, commit: str, path: str) -> str:
    data = subprocess.check_output(['git', '-C', str(repo), 'show', f'{commit}:{path}'])
    return hashlib.sha256(data).hexdigest()


def validate_local() -> dict:
    if not SCHEMA.exists(): fail('missing-schema')
    if not DATA.exists(): fail('missing-data')
    if not DOC.exists(): fail('missing-doc')
    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    data = yaml.safe_load(DATA.read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(data, schema)
    if data['schema'] != 'rhgd-provider-contract-freshness/1': fail('schema-id')
    if data['unit'] != 'U-RHGD-11-PGA-PROVIDER-STRUCTURAL-DRIFT-RECONCILIATION': fail('unit')
    p = data['provider']
    if p['before'] != PGA_BEFORE or p['after'] != PGA_AFTER: fail('provider-refs')
    if p['classification'] != 'HEAD_DRIFT_CONTRACTS_IDENTICAL': fail('classification')
    if set(p['changed_paths']) != EXPECTED_CHANGED: fail('changed-paths')
    if data['consumer_effect']['historical_u08_pin_rewritten'] is not False: fail('historical-pin-rewrite')
    if data['consumer_effect']['functional_reconciliation_required'] is not False: fail('functional-reconciliation')
    if data['consumer_effect']['next_unit_may_use_provider_head'] != PGA_AFTER: fail('next-unit-head')
    if data['consumer_effect']['rule'] != 'semantic_validity_tracks_consumed_artifact_identity_not_unrelated_provider_head_drift': fail('rule')
    artifacts = {x['path']: x for x in data['consumed_artifacts']}
    if set(artifacts) != set(CONSUMED): fail('artifact-set')
    for path, digest in CONSUMED.items():
        x = artifacts[path]
        if x['sha256_before'] != digest or x['sha256_after'] != digest or x['identical'] is not True:
            fail('artifact:'+path)
    expected_gates = {
        'DELTA_INVENTORY': 'PASS',
        'LEARNING_PRESERVED': 'PASS',
        'PGA_HEAD_ANCESTRY': 'PASS',
        'CONSUMED_ARTIFACT_IDENTITY': 'PASS',
        'NO_CONSUMED_SEMANTIC_PATH_DELTA': 'PASS',
        'AUTHORITY_BOUNDARY_UNCHANGED': 'PASS',
        'HISTORICAL_EVIDENCE_IMMUTABLE': 'PASS',
        'FUNCTIONAL_RECONCILIATION_REQUIRED': 'NO',
        'PRODUCTION_PROMOTION': 'NO',
    }
    if data['gates'] != expected_gates: fail('gates')
    doc = DOC.read_text(encoding='utf-8')
    for marker in ('HEAD_DRIFT_CONTRACTS_IDENTICAL', 'hash', 'U-PGA-10', 'não reescreve U08', 'STANDBY_CANDIDATE'):
        if marker not in doc: fail('doc:'+marker)
    return data


def validate_external(suite_root: Path, data: dict) -> None:
    pga = suite_root / 'pga'
    if not pga.joinpath('.git').exists(): fail('missing-pga-repo')
    subprocess.check_call(['git','-C',str(pga),'merge-base','--is-ancestor',PGA_BEFORE,PGA_AFTER])
    subprocess.check_call(['git','-C',str(pga),'merge-base','--is-ancestor',PGA_AFTER,'HEAD'])
    changed = set(git(pga, 'diff', '--name-only', f'{PGA_BEFORE}..{PGA_AFTER}').splitlines())
    if changed != EXPECTED_CHANGED: fail('external-changed-paths')
    if any(path.startswith(FORBIDDEN_PREFIXES) for path in changed): fail('semantic-path-changed')
    for path, digest in CONSUMED.items():
        if blob_sha(pga, PGA_BEFORE, path) != digest: fail('before-hash:'+path)
        if blob_sha(pga, PGA_AFTER, path) != digest: fail('after-hash:'+path)
    print('PGA_PROVIDER_EXTERNAL_IDENTITY=PASS')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--suite-root', type=Path)
    args = ap.parse_args()
    data = validate_local()
    if args.suite_root:
        validate_external(args.suite_root.resolve(), data)
    print('RHGD_U11_PGA_PROVIDER_STRUCTURAL_DRIFT=PASS')


if __name__ == '__main__':
    main()
