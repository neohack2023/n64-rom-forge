from pathlib import Path
import argparse, collections, json, math, re, struct, zlib

def entropy(data):
    if not data: return 0.0
    counts=collections.Counter(data)
    n=len(data)
    return -sum((c/n)*math.log2(c/n) for c in counts.values())

def printable_strings(data, min_len=6, limit=32):
    out=[]
    for m in re.finditer(rb"[ -~]{%d,}" % min_len, data):
        out.append({"offset":m.start(),"text":m.group()[:160].decode("ascii","replace")})
        if len(out)>=limit: break
    return out

def monotonic_u32_runs(data, min_entries=6, limit=24):
    words=[struct.unpack_from(">I",data,i)[0] for i in range(0,len(data)-3,4)]
    runs=[]; start=None; prev=None
    for i,v in enumerate(words):
        valid=0 <= v <= len(data) and v % 4 == 0
        if valid and (prev is None or v >= prev):
            if start is None: start=i
            prev=v
        else:
            if start is not None and i-start >= min_entries:
                vals=words[start:i]
                runs.append({"offset":start*4,"entries":len(vals),"first":vals[0],"last":vals[-1]})
            start=i if valid else None; prev=v if valid else None
        if len(runs)>=limit: break
    return runs
def compression_candidates(data):
    out=[]
    if len(data)>=8:
        be=struct.unpack_from(">I",data,0)[0]
        le=struct.unpack_from("<I",data,0)[0]
        for endian,value in (("be",be),("le",le)):
            if len(data) < value <= 128*1024*1024:
                out.append({"kind":"size_prefix","endian":endian,"declared_size":value,"ratio":round(value/max(1,len(data)),3)})
    for mode,wbits in (("zlib",15),("raw_deflate",-15),("gzip",31)):
        starts=[0,4,8]
        for start in starts:
            if start>=len(data): continue
            try:
                dec=zlib.decompress(data[start:],wbits)
                if dec:
                    out.append({"kind":mode,"start":start,"decoded_size":len(dec),"decoded_prefix16":dec[:16].hex()})
            except Exception:
                pass
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    root=Path(args.directory)
    rows=[]
    for path in sorted(root.glob("section_*.bin")):
        data=path.read_bytes()
        rows.append({
            "file":path.name,
            "size":len(data),
            "entropy":round(entropy(data),4),
            "prefix32":data[:32].hex(),
            "strings":printable_strings(data),
            "monotonic_u32_runs":monotonic_u32_runs(data),
            "compression_candidates":compression_candidates(data),
            "zero_fraction":round(data.count(0)/max(1,len(data)),4),
        })
    report={"schema":"n64.section_profile.v1","directory":str(root),"sections":rows}
    Path(args.out).write_text(json.dumps(report,indent=2),encoding="utf-8")
    summary={
        "sections":len(rows),
        "with_strings":[r["file"] for r in rows if r["strings"]],
        "with_monotonic_tables":[r["file"] for r in rows if r["monotonic_u32_runs"]],
        "with_compression_candidates":[r["file"] for r in rows if r["compression_candidates"]],
        "high_entropy":[[r["file"],r["entropy"],r["size"]] for r in rows if r["entropy"]>=7.5],
        "low_entropy":[[r["file"],r["entropy"],r["size"]] for r in rows if r["size"] and r["entropy"]<=3.0],
    }
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
