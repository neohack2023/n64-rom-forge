from pathlib import Path
import argparse, json, struct, zlib

def probe(data):
    if len(data) < 8:
        return []
    declared=struct.unpack_from(">I",data,0)[0]
    if not (len(data) < declared <= 64*1024*1024):
        return []
    out=[]
    for start in (4,5,8):
        if start>=len(data): continue
        for name,wbits in (("zlib",15),("raw_deflate",-15),("gzip",31)):
            try:
                obj=zlib.decompressobj(wbits)
                dec=obj.decompress(data[start:],declared+1)
                dec+=obj.flush()
                if obj.eof and len(dec)==declared:
                    out.append({
                        "codec":name,"start":start,
                        "declared_size":declared,
                        "decoded_size":len(dec),
                        "unused_bytes":len(obj.unused_data),
                        "decoded_prefix16":dec[:16].hex(),
                    })
            except Exception:
                pass
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--glob",default="*.bin")
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    root=Path(args.root)
    rows=[]
    checked=0
    plausible=0
    for path in sorted(root.rglob(args.glob)):
        data=path.read_bytes()
        checked+=1
        declared=struct.unpack_from(">I",data,0)[0] if len(data)>=4 else None
        if declared is not None and len(data) < declared <= 64*1024*1024:
            plausible+=1
        hits=probe(data)
        if hits:
            rows.append({
                "path":str(path.relative_to(root)).replace("\\","/"),
                "size":len(data),"hits":hits,
            })
    report={
        "schema":"n64.strict_compression_probe.v1",
        "root":str(root),"glob":args.glob,
        "checked":checked,"plausible_declared_size":plausible,
        "decoded_records":len(rows),"rows":rows,
    }
    Path(args.out).write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({
        "checked":checked,
        "plausible_declared_size":plausible,
        "decoded_records":len(rows),
        "samples":rows[:12],
    },indent=2))

if __name__=="__main__":
    main()
