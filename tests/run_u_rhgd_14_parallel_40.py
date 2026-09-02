#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys,time,threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CASES=[f'U14-W{i:02d}' for i in range(1,41)]

def run_one(case: str, hold_ms: int, state: dict, lock: threading.Lock) -> dict:
    with lock:
        state['active']+=1
        state['max_parallel']=max(state['max_parallel'],state['active'])
    try:
        p=subprocess.run([sys.executable,str(ROOT/'tests/u14_parallel_cases.py'),case,'--hold-ms',str(hold_ms)],capture_output=True,text=True,cwd=ROOT,timeout=30)
        try: r=json.loads(p.stdout.strip().splitlines()[-1])
        except Exception: r={'unit':case,'status':'FAIL','detail':'invalid-worker-output','stdout':p.stdout[-500:],'stderr':p.stderr[-500:]}
        r['process_rc']=p.returncode
        return r
    finally:
        with lock: state['active']-=1

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--jobs',type=int,default=4); ap.add_argument('--case-start',type=int,default=1); ap.add_argument('--case-end',type=int,default=40); ap.add_argument('--hold-ms',type=int,default=100); ap.add_argument('--json-out',type=Path); args=ap.parse_args()
    if not (1 <= args.case_start <= args.case_end <= 40): raise SystemExit('invalid case range')
    selected=CASES[args.case_start-1:args.case_end]
    if not (1 <= args.jobs <= len(selected)): raise SystemExit('jobs must be within selected case count')
    started=time.time_ns()//1_000_000
    state={'active':0,'max_parallel':0}; lock=threading.Lock(); results=[]
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futures={ex.submit(run_one,case,args.hold_ms,state,lock):case for case in selected}
        for fut in as_completed(futures):
            try: results.append(fut.result())
            except Exception as exc: results.append({'unit':futures[fut],'status':'FAIL','detail':f'{type(exc).__name__}:{exc}','process_rc':2})
    results.sort(key=lambda x:x['unit'])
    ended=time.time_ns()//1_000_000
    passed=sum(r.get('status')=='PASS' and r.get('process_rc')==0 for r in results)
    expected=len(selected)
    summary={'schema':'rhgd-u14-parallel-40-shard/2','global_worker_count':40,'case_start':args.case_start,'case_end':args.case_end,'selected_units':expected,'physical_slots':args.jobs,'max_parallel_observed':state['max_parallel'],'passed':passed,'failed':expected-passed,'started_ms':started,'ended_ms':ended,'elapsed_ms':ended-started,'units':results}
    if args.json_out: args.json_out.write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='units'},sort_keys=True))
    if passed!=expected or state['max_parallel']<min(args.jobs,expected): raise SystemExit(2)
    print(f'RHGD_U14_PARALLEL_SHARD=PASS cases={args.case_start}-{args.case_end} slots={args.jobs}')
if __name__=='__main__': main()
