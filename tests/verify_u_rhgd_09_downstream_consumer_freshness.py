#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / 'contratos/rhgd-0.0.1/downstream-consumer-freshness.schema.json'
DATA = ROOT / 'dados/rhgd-0.0.1/U-RHGD-09-downstream-consumer-freshness.yaml'
DOC = ROOT / 'docs/arquitetura/09-downstream-consumer-freshness.md'
U08_CLOSED_SAFE_POINT = '13b6e0aadcb59902312915130d1bc6cd2bc81fd4'
U282_UNIT = 'U282-PGH-SUITE-POST-U278-FIXED-POINT-REFRESH'
U282_DATA = 'dados/pgh-2.0/U282-suite-post-u278-fixed-point-refresh.yaml'


def fail(msg: str) -> None:
    print('RHGD_U09_DOWNSTREAM_CONSUMER_FRESHNESS=FAIL', msg)
    raise SystemExit(2)


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def local_validate() -> dict:
    if not SCHEMA.exists(): fail('missing-schema')
    if not DATA.exists(): fail('missing-data')
    if not DOC.exists(): fail('missing-doc')
    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    data = yaml.safe_load(DATA.read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(data, schema)
    if data['schema'] != 'rhgd-downstream-consumer-freshness/1': fail('schema-id')
    if data['unit'] != 'U-RHGD-09-POST-U08-SUITE-INTEGRATION-CHECK': fail('unit')
    if data['producer']['closed_safe_point'] != U08_CLOSED_SAFE_POINT: fail('producer-safe-point')
    if data['consumer']['unit'] != U282_UNIT: fail('consumer-unit')
    if data['consumer']['freshness'] != 'STALE': fail('freshness')
    if data['consumer']['classification'] != 'BLOCKED_ACTIVE_OWNER_STALE': fail('classification')
    if data['consumer']['mutation_allowed'] is not False: fail('mutation-allowed')
    if data['consumer']['required_next_action'] != 'owner_reconcile_after_active_work_or_within_own_zone': fail('next-action')
    gates = data['gates']
    expected = {
        'PRODUCER_SAFE_POINT': 'PASS',
        'CONSUMER_PIN_READ': 'PASS',
        'STALE_DETECTED': 'PASS',
        'ACTIVE_OWNER_RESPECTED': 'PASS',
        'AUTO_MUTATION': 'BLOCKED',
        'DOWNSTREAM_SYNCHRONIZED': 'NO',
        'NO_FALSE_FIXED_POINT': 'PASS',
    }
    if gates != expected: fail('gates')
    doc = DOC.read_text(encoding='utf-8')
    for marker in ('BLOCKED_ACTIVE_OWNER_STALE', 'safe point fechado', 'não editar', 'U282', U08_CLOSED_SAFE_POINT[:12]):
        if marker not in doc: fail('doc:'+marker)
    return data


def external_validate(root: Path, data: dict) -> None:
    rhgd = root / 'rhgd'
    core = root / 'protocolo-governanca-heterogenea'
    if not rhgd.joinpath('.git').exists(): fail('missing-rhgd-repo')
    if not core.joinpath('.git').exists(): fail('missing-core-repo')
    # Producer safe point must remain an ancestor of the current in-progress RHGD head.
    subprocess.check_call(['git','-C',str(rhgd),'merge-base','--is-ancestor',U08_CLOSED_SAFE_POINT,'HEAD'])
    observed_core = data['consumer']['observed_core_head']
    observed_rhgd = data['producer']['observed_active_head']
    subprocess.check_call(['git','-C',str(core),'merge-base','--is-ancestor',observed_core,'HEAD'])
    subprocess.check_call(['git','-C',str(rhgd),'merge-base','--is-ancestor',observed_rhgd,'HEAD'])
    # Reconstruct the observation from the exact consumer commit so later owner progress
    # cannot rewrite the historical classification.
    u282 = yaml.safe_load(git(core, 'show', f'{observed_core}:{U282_DATA}'))
    manifest = yaml.safe_load(git(core, 'show', f'{observed_core}:manifesto.yaml'))
    sw = manifest.get('trabalho_compartilhado') or {}
    if sw.get('unidade') != U282_UNIT: fail('u282-not-active-owner-at-observation')
    pinned = (u282.get('snapshot_refs') or {}).get('rhgd')
    if pinned != data['consumer']['observed_rhgd_pin']: fail('consumer-pin-observation-mismatch')
    if pinned == U08_CLOSED_SAFE_POINT: fail('expected-stale-but-fresh')
    if data['consumer']['observed_owner'] != sw.get('agente'): fail('consumer-owner')
    if data['consumer']['observed_owner_until'] != sw.get('previsao_termino'): fail('consumer-owner-until')
    print('DOWNSTREAM_EXTERNAL_OBSERVATION=PASS')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--suite-root', type=Path)
    args = ap.parse_args()
    data = local_validate()
    if args.suite_root:
        external_validate(args.suite_root.resolve(), data)
    print('RHGD_U09_DOWNSTREAM_CONSUMER_FRESHNESS=PASS')


if __name__ == '__main__':
    main()
