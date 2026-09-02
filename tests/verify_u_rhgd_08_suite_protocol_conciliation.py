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
SCHEMA = ROOT / 'contratos/rhgd-0.0.1/suite-protocol-conciliation.schema.json'
DATA = ROOT / 'dados/rhgd-0.0.1/U-RHGD-08-suite-protocol-conciliation.yaml'
DOC = ROOT / 'docs/arquitetura/08-suite-protocol-conciliation.md'
BASE_RHGD = 'ee24a3916e964c7ec624b666daa035aa6f4e97c5'
EXPECTED_HEADS = {
    'pgd': 'fa63a046e79e28d512dd901c43629d47a5bdea89',
    'pga': '5d1dfd93b0525db26b44efaea8bdbc56f25c185c',
}
CONTROL_PLANE_SAFE_POINT = '9408814f4af6b73c743b0dc35661caee0da5adca'
PGH_U278 = '1832fa24375a1e2f3cc207b163f1a42d0acc2042'
CONTRACT_HASHES = {
    'pgd/contratos/pgd-1.0/rhgd-federation.schema.json': '3135f6cee8de163d55c9782b1b1de300359a0e2936f79f2a243a03941fefdc52',
    'pgd/contratos/pgd-1.0/incremental-information-exchange.schema.json': 'aea5c1c7c6e8f15c55eba596e1d9b4a9bdf5bbc34c15c2fcc47fafae4b496964',
    'pga/contratos/pga-1.0/network-service-agents.schema.json': '504df737545226ac6837fea6299d4ccd0732f9197bcdadf948f03886209a361a',
    'pga/contratos/pga-1.0/deterministic-priority-policy.schema.json': '2d84c843b9d8f4debcea7efe58a44ec7b8d31d2dfabf1ed5eb393dffd9b71126',
    'protocolo-governanca-heterogenea/contratos/pgh-2.0/deterministic-election-fabric.schema.json': '5005c84423c1a09dab686d2640c6faf040f548cf6eedcfe688f55ba05c9eb6a3',
    'pgh-distributed-session-control-plane/config/3.0/context-sync.yaml': 'e01af951c82e4fb56e00c511eb91cc17a22d855492e36a25ef6e5de6e96a22c0',
}


def fail(msg: str) -> None:
    print('RHGD_U08_SUITE_PROTOCOL_CONCILIATION=FAIL', msg)
    raise SystemExit(2)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def validate_local() -> dict:
    if not SCHEMA.exists(): fail('missing-schema')
    if not DATA.exists(): fail('missing-data')
    if not DOC.exists(): fail('missing-doc')
    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    data = yaml.safe_load(DATA.read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(data, schema)

    if data['schema'] != 'rhgd-suite-protocol-conciliation/1': fail('schema-id')
    if data['unit'] != 'U-RHGD-08-R1-SUITE-PROTOCOL-CONCILIATION': fail('unit')
    if data['release']['version'] != '0.0.1' or data['release']['state'] != 'standby_candidate': fail('release-state')
    if data['refs']['RHGD_BASE'] != BASE_RHGD: fail('rhgd-base')
    if data['refs']['PGH_U278_SAFE_POINT'] != PGH_U278: fail('pgh-safe-point')
    for k, v in EXPECTED_HEADS.items():
        key = {'pgd':'PGD','pga':'PGA'}[k]
        if data['refs'][key] != v: fail('ref:'+key)
    if data['refs']['CONTROL_PLANE'] != CONTROL_PLANE_SAFE_POINT: fail('ref:CONTROL_PLANE')

    boundaries = data['authority_boundaries']
    expected = {
        'PGA': 'policy_authority_priority_gates_no_runtime',
        'PGH': 'semantic_authorization_context_knowledge_evidence',
        'PGD': 'runtime_assignment_queue_lease_retry_recovery_watermark',
        'RHGD': 'federation_discovery_transport_route_observation_no_scheduler',
        'MSGCD': 'aggregation_integration_no_independent_authority',
    }
    if boundaries != expected: fail('authority-boundaries')

    consumed = {x['id']: x for x in data['consumed_contracts']}
    required = {
        'pgd-rhgd-federation/1',
        'pgd-incremental-information-exchange/1',
        'pga-network-service-agents/1',
        'pga-deterministic-priority-policy/1',
        'CT-PGH2-DETERMINISTIC-ELECTION-FABRIC@1.0.0',
        'pgh-context-sync/1',
    }
    if set(consumed) != required: fail('consumed-contract-set')

    if data['network_policy']['default_scope'] != 'private': fail('private-default')
    if data['network_policy']['join'] != 'explicit-only': fail('explicit-join')
    if data['network_policy']['private_resources_shared_implicitly'] is not False: fail('implicit-private-sharing')
    roles = [x['role'] for x in data['network_policy']['service_agents']]
    if roles != ['network_control_agent', 'distributed_processing_agent']: fail('service-agent-roles')
    if any(x['runtime_owner'] != 'PGD/runtime-owner' for x in data['network_policy']['service_agents']): fail('service-agent-runtime-owner')
    if data['network_policy']['network_federation_owner'] != 'RHGD/network-owner': fail('network-owner')

    maturity = data['maturity']
    if maturity['contractual_federation'] != 'PASS': fail('contractual-federation')
    if maturity['live_capability_discovery'] != 'NOT_VERIFIED': fail('live-capability-claim')
    if maturity['real_network_federation'] != 'NOT_VERIFIED': fail('real-network-claim')
    if maturity['production'] != 'BLOCKED': fail('production-claim')
    if maturity['tee_attestation'] != 'OPTIONAL_NOT_REQUIRED_FOR_U08': fail('tee-status')
    if maturity['upstream_adapters'] != 'OPTIONAL_NOT_REQUIRED_FOR_U08': fail('upstream-adapters-status')

    forbidden = {'scheduler','queue','lease','admission','retry','recovery','runtime_state','priority_authority'}
    if forbidden.intersection(data['rhgd_owns']): fail('rhgd-ownership-expansion')
    if 'FederatedDestinationMatcher' != data['federated_destination_selection']['canonical_type']: fail('matcher-type')
    if data['federated_destination_selection']['authority_effect'] != 'NONE': fail('matcher-authority')

    gates = data['gates']
    for g in ('DELTA_INVENTORY','LEARNING_PRESERVED','AUTHORITY_BOUNDARY','NO_SECOND_SCHEDULER','PGD_CONTRACTS','PGA_POLICY','PGH_SAFE_POINT','MSGCD_BOUNDARY','CONTEXT_SYNC_BOUNDARY','RELEASE_IMMUTABILITY'):
        if gates.get(g) != 'PASS': fail('gate:'+g)
    if gates.get('LIVE_CAPABILITY_DISCOVERY') != 'NOT_VERIFIED': fail('gate:LIVE_CAPABILITY_DISCOVERY')
    if gates.get('REAL_NETWORK_FEDERATION') != 'NOT_VERIFIED': fail('gate:REAL_NETWORK_FEDERATION')
    if gates.get('PRODUCTION') != 'BLOCKED': fail('gate:PRODUCTION')

    doc = DOC.read_text(encoding='utf-8')
    for marker in ('PGD U14', 'PGA U08', 'PGA U09', 'PGH U278', 'RHGD federa', 'MSGCD agrega', 'STANDBY_CANDIDATE', 'capability discovery vivo'):
        if marker not in doc: fail('doc:'+marker)
    return data


def validate_external(root: Path, data: dict) -> None:
    for name, expected in EXPECTED_HEADS.items():
        repo = root / name
        if not repo.joinpath('.git').exists(): fail('external-repo:'+name)
        if git(repo, 'rev-parse', 'HEAD') != expected: fail('external-head:'+name)
    cp = root / 'pgh-distributed-session-control-plane'
    if not cp.joinpath('.git').exists(): fail('external-repo:pgh-distributed-session-control-plane')
    subprocess.check_call(['git','-C',str(cp),'merge-base','--is-ancestor',CONTROL_PLANE_SAFE_POINT,'HEAD'])
    pgh = root / 'protocolo-governanca-heterogenea'
    if not pgh.joinpath('.git').exists(): fail('external-repo:protocolo-governanca-heterogenea')
    subprocess.check_call(['git','-C',str(pgh),'merge-base','--is-ancestor',PGH_U278,'HEAD'])
    for rel, expected in CONTRACT_HASHES.items():
        path = root / rel
        if not path.exists(): fail('external-path:'+rel)
        if sha256(path) != expected: fail('external-hash:'+rel)
    # U08 is contract/reconciliation only: no pre-existing RHGD runtime file may change.
    changed = set(git(ROOT, 'diff', '--name-only', f'{BASE_RHGD}..HEAD').splitlines())
    allowed = {
        'manifesto.yaml','estado.md','competencias.yaml','skills/rhgd/SKILL.md',
        'contratos/rhgd-0.0.1/suite-protocol-conciliation.schema.json',
        'dados/rhgd-0.0.1/U-RHGD-08-suite-protocol-conciliation.yaml',
        'docs/arquitetura/08-suite-protocol-conciliation.md',
        'tests/verify_u_rhgd_08_suite_protocol_conciliation.py',
    }
    illegal = changed - allowed
    if illegal: fail('runtime-drift:'+','.join(sorted(illegal)))
    print('EXTERNAL_REFS=PASS')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--suite-root', type=Path)
    args = ap.parse_args()
    data = validate_local()
    if args.suite_root:
        validate_external(args.suite_root.resolve(), data)
    print('RHGD_U08_SUITE_PROTOCOL_CONCILIATION=PASS')


if __name__ == '__main__':
    main()
