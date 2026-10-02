from pathlib import Path
import argparse,struct,json
from collections import Counter

def runs(buf,min_entries):
    words=[struct.unpack_from(">I",buf,i)[0] for i in range(0,len(buf)-3,4)]
    out=[]; start=None; prev=None
    for wi,v in enumerate(words):
        valid=(0x1000<=v<len(buf) and v%4==0)
        if valid and (prev is None or v>prev):
            if start is None:start=wi
            prev=v
        else:
            if start is not None and wi-start>=min_entries:
                vals=words[start:wi]
                out.append((start*4,vals))
            start=wi if valid else None
            prev=v if valid else None
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("--min-entries",type=int,default=32)
    ap.add_argument("--pair-distance",type=lambda x:int(x,0),default=0x4000)
    ap.add_argument("--out")
    a=ap.parse_args()
    p=Path(a.rom); b=p.read_bytes()
    rs=runs(b,a.min_entries)
    candidates=[]
    for i,(oa,A) in enumerate(rs):
        for ob,B in rs[i+1:]:
            if len(A)!=len(B): continue
            if abs(ob-oa)>a.pair_distance: continue
            valid=sum(1 for x,y in zip(A,B) if 0<=x<=y<=len(b))
            if valid/len(A)<0.95: continue
            contiguous=sum(1 for j in range(len(A)-1) if B[j]==A[j+1])
            prefixes=Counter(b[x:x+4].hex() for x in A if x+4<=len(b))
            candidates.append({
              "table_a":oa,"table_b":ob,"entries":len(A),
              "valid_pair_fraction":round(valid/len(A),4),
              "contiguous_transition_fraction":round(contiguous/max(1,len(A)-1),4),
              "first_start":A[0],"last_end":B[-1],
              "resource_span":B[-1]-A[0],
              "dominant_prefix4":prefixes.most_common(8),
              "score":(valid/len(A))*4+(contiguous/max(1,len(A)-1))*4+(1 if len(A)>=64 else 0)+(1 if B[-1]-A[0]>=0x100000 else 0)
            })
    candidates.sort(key=lambda x:(-x["score"],-x["entries"]))
    out={"schema":"n64.generic_paired_absolute_range_detector.v1","rom":str(p),"candidates":candidates}
    if a.out: Path(a.out).write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"candidate_count":len(candidates),"top":candidates[:12]},indent=2))
if __name__=="__main__": main()
