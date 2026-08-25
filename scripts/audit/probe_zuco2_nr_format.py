#!/usr/bin/env python3
"""Model-blind ZuCo 2.0 task1-NR format probe.

Downloads only seven tiny shared wordbounds files and one representative preprocessed
EEG run (YDG NR1), then inspects MATLAB metadata/keys. No reliability or model analysis.
"""
from __future__ import annotations
import argparse, json, urllib.request, time
from pathlib import Path
from datetime import datetime, timezone

import h5py
from scipy.io import whosmat, loadmat

NODE='2urht'; UA='NeuroSem-ZuCo2-format-probe/1.1'
TARGETS=[f'task1 - NR/Preprocessed/wordbounds_NR{i}.mat' for i in range(1,8)] + ['task1 - NR/Preprocessed/YDG/gip_YDG_NR1_EEG.mat']

def get_json(url,retries=4):
    last=None
    for a in range(retries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/vnd.api+json'})
            with urllib.request.urlopen(req,timeout=60) as r: return json.load(r)
        except Exception as e:
            last=e; time.sleep(2**a)
    raise RuntimeError(f'OSF request failed: {url}: {last}')

def paged(url):
    while url:
        o=get_json(url)
        yield from o.get('data',[])
        url=(o.get('links') or {}).get('next')

def child_url(row):
    rel=(((row.get('relationships') or {}).get('files') or {}).get('links') or {}).get('related')
    return rel.get('href') if isinstance(rel,dict) else rel

def walk(url,prefix='',out=None):
    out={} if out is None else out
    for row in paged(url):
        a=row.get('attributes') or {}; name=str(a.get('name') or ''); kind=str(a.get('kind') or '')
        p=f'{prefix}/{name}' if prefix else name
        if kind=='file': out[p]=(row.get('links') or {}).get('download')
        elif kind=='folder' and any(t.startswith(p+'/') or t==p for t in TARGETS):
            u=child_url(row)
            if u: walk(u,p,out)
    return out

def inventory():
    out={}
    for prov in paged(f'https://api.osf.io/v2/nodes/{NODE}/files/'):
        u=child_url(prov)
        if u: walk(u,'',out)
    return out

def download(url,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    req=urllib.request.Request(url,headers={'User-Agent':UA})
    with urllib.request.urlopen(req,timeout=300) as r, path.open('wb') as f:
        while True:
            b=r.read(1024*1024)
            if not b: break
            f.write(b)

def summarize_hdf5(path: Path):
    out={'format':'matlab_v7.3_hdf5','top_level':[]}
    with h5py.File(path,'r') as f:
        for name,obj in f.items():
            rec={'name':name,'kind':'dataset' if isinstance(obj,h5py.Dataset) else 'group'}
            if isinstance(obj,h5py.Dataset):
                rec['shape']=list(obj.shape)
                rec['dtype']=str(obj.dtype)
            else:
                rec['n_children']=len(obj.keys())
                rec['children_preview']=list(obj.keys())[:25]
            out['top_level'].append(rec)
    return out

def summarize_mat(path,load_small=False):
    out={'path':str(path),'size_bytes':path.stat().st_size}
    if h5py.is_hdf5(path):
        out.update(summarize_hdf5(path))
        return out
    out['format']='matlab_pre_v7.3'
    out['whosmat']=[]
    for name,shape,cls in whosmat(path): out['whosmat'].append({'name':name,'shape':list(shape),'class':cls})
    if load_small:
        d=loadmat(path,simplify_cells=True)
        out['keys']=[k for k in d if not k.startswith('__')]
        for k in out['keys']:
            v=d[k]
            out.setdefault('value_types',{})[k]=type(v).__name__
            if hasattr(v,'shape'): out.setdefault('value_shapes',{})[k]=list(v.shape)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-root',type=Path,default=Path('data/raw/zuco2_probe')); ap.add_argument('--output-dir',type=Path,default=Path('outputs/zuco2_nr_format_probe/latest')); args=ap.parse_args()
    idx=inventory(); missing=[t for t in TARGETS if t not in idx or not idx[t]]
    if missing: raise SystemExit(f'missing OSF targets: {missing}')
    root=args.data_root.resolve(); outdir=args.output_dir.resolve(); outdir.mkdir(parents=True,exist_ok=True)
    mats=[]
    for t in TARGETS:
        p=root/t
        if not p.exists(): download(idx[t],p)
        mats.append(summarize_mat(p,load_small='wordbounds_' in t))
    summary={'created_at_utc':datetime.now(timezone.utc).isoformat(),'analysis_status':'model-blind format probe; no EEG values used for reliability/model analysis','release':'ZuCo 2.0','osf_node':NODE,'task':'task1 - NR','representative_subject':'YDG','representative_run':'NR1','targets':mats,'guardrail':'Use only to freeze signal structure, item alignment, and materialization plan before any EEG reliability.'}
    (outdir/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':'ok','output_dir':str(outdir)},indent=2))
if __name__=='__main__': main()
