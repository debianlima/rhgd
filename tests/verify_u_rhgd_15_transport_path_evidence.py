from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
S=R/'contratos/rhgd-0.0.1/transport-path-evidence.schema.json'
M=R/'transport_path_evidence.py'
E=R/'dados/rhgd-0.0.1/U-RHGD-15-transport-path-evidence.yaml'
D=R/'docs/arquitetura/15-transport-path-evidence-netmaker.md'
T=R/'dados/rhgd-0.0.1/U-RHGD-15-telemetria-inicio.json'

def fail(x): print('RHGD_U15_TRANSPORT_PATH=FAIL',x); raise SystemExit(2)
def main():
    if not T.exists() or json.loads(T.read_text())['event']!='telemetria_inicio': fail('telemetry-start')
    for p in (S,M,E,D):
        if not p.exists(): fail('missing:'+str(p.relative_to(R)))
    text=(R/'rhgd_cognitive_dag.py').read_text(encoding='utf-8')
    for marker in ('TransportPathEvidence','path_evidence','transport_path_bonus'):
        if marker not in text: fail('matcher:'+marker)
    doc=D.read_text(encoding='utf-8')
    for marker in ('NETMAKER','WIREGUARD_DIRECT','IPSEC','source_of_truth=false','scheduler=false','assignment=false'):
        if marker not in doc: fail('doc:'+marker)
    print('RHGD_U15_TRANSPORT_PATH=PASS')
if __name__=='__main__': main()
