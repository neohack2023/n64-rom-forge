from pathlib import Path
import argparse, json, re, struct

def idx(path):
    m=re.search(r"section_(\d+)_",path.name)
    return int(m.group(1)) if m else 9999

def scan_table(data, target_size, start, min_entries=4):
    vals=[]; sentinel=None
    for off in range(start,len(data)-3,4):
        v=struct.unpack_from(">I",data,off)[0]
        if v in (0xFFFFFFFF,0xFFFFFFFE):
            sentinel=v; break
        if v > target_size:
            break
        if vals and v < vals[-1]:
            break
        vals.append(v)
    if len(vals)<min_entries:
        return None
    nonzero=sum(1 for v in vals if v)
    if nonzero<2:
        return None
    return {
        "table_offset":start,
        "entries":len(vals),
        "first":vals[0],
        "last":vals[-1],
        "sentinel":None if sentinel is None else f"0x{sentinel:08X}",
        "target_fraction":round(vals[-1]/max(1,target_size),4),
        "sample":[f"0x{x:X}" for x in vals[:16]],
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    files=sorted(Path(args.directory).glob("section_*.bin"),key=idx)
    pairs=[]
    for a,b in zip(files,files[1:]):
        A=a.read_bytes(); B=b.read_bytes()
        candidates=[]
        for start in range(0,min(len(A),128),4):
            row=scan_table(A,len(B),start)
            if row:
                row["starts_at_zero"]=row["first"]==0
                row["alignment16"]=all(int(x,16)%16==0 for x in row["sample"][:8])
                candidates.append(row)
        candidates.sort(key=lambda r:(not r["starts_at_zero"],-r["entries"],-r["target_fraction"],r["table_offset"]))
        if candidates:
            best=candidates[0]
            pairs.append({
                "index":idx(a),
                "table_section":a.name,
                "payload_section":b.name,
                "table_size":len(A),
                "payload_size":len(B),
                "best":best,
                "alternates":candidates[1:5],
            })
    high_confidence=[
        x for x in pairs
        if x["best"]["starts_at_zero"]
        and x["table_size"] < x["payload_size"]
        and x["best"]["target_fraction"] >= 0.9
    ]
    report={
        "schema":"n64.adjacent_lut_detector.v1",
        "directory":str(Path(args.directory)),
        "pairs":pairs,
        "high_confidence_pairs":[x["index"] for x in high_confidence],
    }
    Path(args.out).write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({
        "pair_count":len(pairs),
        "high_confidence_count":len(high_confidence),
        "high_confidence_pairs":[{
            "pair":f'{x["index"]}->{x["index"]+1}',
            "entries":x["best"]["entries"],
            "last":x["best"]["last"],
            "payload_size":x["payload_size"],
            "target_fraction":x["best"]["target_fraction"],
        } for x in high_confidence]
    },indent=2))

if __name__=="__main__":
    main()
