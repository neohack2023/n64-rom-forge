from pathlib import Path
import argparse, hashlib, json, re, struct

def section_index(name):
    m=re.search(r"section_(\d+)_",name)
    return int(m.group(1)) if m else None

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("detector_report")
    ap.add_argument("section_dir")
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--report",required=True)
    args=ap.parse_args()

    det=json.loads(Path(args.detector_report).read_text(encoding="utf-8"))
    root=Path(args.section_dir)
    files={section_index(p.name):p for p in root.glob("section_*.bin")}
    selected=set(det.get("high_confidence_pairs") or [])
    out_root=Path(args.out_dir)
    out_root.mkdir(parents=True,exist_ok=True)
    pairs=[]
    for row in det["pairs"]:
        i=row["index"]
        if i not in selected:
            continue
        table=files[i].read_bytes()
        payload=files[i+1].read_bytes()
        best=row["best"]
        start=best["table_offset"]
        values=[
            struct.unpack_from(">I",table,start+j*4)[0]
            for j in range(best["entries"])
        ]
        pair_dir=out_root/f"pair_{i:02d}_{i+1:02d}"
        pair_dir.mkdir(exist_ok=True)
        items=[]
        for j,(a,b) in enumerate(zip(values,values[1:])):
            chunk=payload[a:b]
            path=pair_dir/f"item_{j:04d}_{a:08X}_{b:08X}.bin"
            path.write_bytes(chunk)
            items.append({
                "index":j,"start":a,"end":b,"size":len(chunk),
                "sha256":sha256(chunk),"prefix16":chunk[:16].hex(),
                "dump":str(path),
            })
        tail=payload[values[-1]:]
        pairs.append({
            "table_section":i,"payload_section":i+1,
            "table_offset":start,"boundary_count":len(values),
            "item_count":len(items),"payload_size":len(payload),
            "last_boundary":values[-1],"tail_size":len(tail),
            "items":items,
        })
    report={
        "schema":"n64.adjacent_lut_unpack.v1",
        "detector_report":str(Path(args.detector_report)),
        "section_dir":str(root),
        "pair_count":len(pairs),
        "pairs":pairs,
    }
    Path(args.report).write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({
        "pair_count":len(pairs),
        "total_items":sum(x["item_count"] for x in pairs),
        "pairs":[{
            "pair":f'{x["table_section"]}->{x["payload_section"]}',
            "items":x["item_count"],
            "payload_size":x["payload_size"],
            "tail_size":x["tail_size"],
        } for x in pairs],
    },indent=2))

if __name__=="__main__":
    main()
