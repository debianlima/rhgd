#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CASES=[f'U14-W{i:02d}' for i in range(1,41)]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--jobs',type=int,default=40); ap.add_argument('--json-out',type=Path); args=ap.parse_args()
    if args.jobs!=40: raise SystemExit('U14 gate requires exactly 40 parallel worker slots')
    started=time.time_ns()//1_000_000
    procs=[]
    for case in CASES:
        p=subprocess.Popen([sys.executable,str(ROOT/'tests/u14_parallel_cases.py'),case,'--hold-ms','250'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,cwd=ROOT)
        procs.append((case,p))
    alive_after_spawn=sum(1 for _,p in procs if p.poll() is None)
    results=[]
    for case,p in procs:
        out,err=p.communicate(timeout=20)
        try: r=json.loads(out.strip().splitlines()[-1])
        except Exception: r={'unit':case,'status':'FAIL','detail':'invalid-worker-output','stdout':out[-500:],'stderr':err[-500:]}
        r['process_rc']=p.returncode; results.append(r)
    ended=time.time_ns()//1_000_000
    passed=sum(r.get('status')=='PASS' and r.get('process_rc')==0 for r in results)
    summary={'schema':'rhgd-u14-parallel-40/1','requested_workers':40,'spawned_workers':len(procs),'alive_after_spawn':alive_after_spawn,'passed':passed,'failed':40-passed,'started_ms':started,'ended_ms':ended,'elapsed_ms':ended-started,'units':results}
    if args.json_out: args.json_out.write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='units'},sort_keys=True))
    if passed!=40 or alive_after_spawn<35: raise SystemExit(2)
    print('RHGD_U14_PARALLEL_40=PASS')
if __name__=='__main__': main()
