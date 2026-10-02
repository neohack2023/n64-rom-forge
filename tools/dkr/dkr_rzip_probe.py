from pathlib import Path
import argparse, hashlib, json, struct, zlib

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def decode_dkr_rzip(data):
    if len(data) < 6:
        return None
    declared=struct.unpack_from("<I",data,0)[0]
    level=data[4]
    if declared <= 0 or declared > 64*1024*1024:
        return None
    if level != 0x09:
        return None
    try:
        obj=zlib.decompressobj(-15)
        decoded=obj.decompress(data[5:],declared+1)
        decoded+=obj.flush()
    except zlib.error:
        return None
    if not obj.eof or len(decoded) != declared:
        return None
    padding=obj.unused_data
    if padding and any(padding):
        return None
    return {
        "declared_size":declared,
        "compression_level":level,
        "decoded":decoded,
        "padding_bytes":len(padding),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--glob",default="*.bin")
    ap.add_argument("--out",required=True)
    ap.add_argument("--decoded-dir")
    args=ap.parse_args()
    root=Path(args.root)
    decoded_root=Path(args.decoded_dir) if args.decoded_dir else None
    if decoded_root:
        decoded_root.mkdir(parents=True,exist_ok=True)
    rows=[]
    checked=0
    header_candidates=0
    for path in sorted(root.rglob(args.glob)):
        data=path.read_bytes()
        checked+=1
        if len(data)>=5 and data[4]==0x09:
            declared=struct.unpack_from("<I",data,0)[0]
            if 0 < declared <= 64*1024*1024:
                header_candidates+=1
        hit=decode_dkr_rzip(data)
        if not hit:
            continue
        decoded=hit.pop("decoded")
        row={
            "path":str(path.relative_to(root)).replace("\\","/"),
            "compressed_size":len(data),
            "decoded_size":len(decoded),
            "ratio":round(len(decoded)/max(1,len(data)),4),
            "padding_bytes":hit["padding_bytes"],
            "decoded_sha256":sha256(decoded),
            "decoded_prefix32":decoded[:32].hex(),
        }
        if decoded_root:
            out=decoded_root/(str(path.relative_to(root)).replace("\\","__")+".decoded.bin")
            out.write_bytes(decoded)
            row["decoded_path"]=str(out)
        rows.append(row)
    report={
        "schema":"n64.dkr_rzip_probe.v1",
        "root":str(root),"glob":args.glob,
        "checked":checked,
        "header_candidates":header_candidates,
        "decoded_records":len(rows),
        "rows":rows,
    }
    Path(args.out).write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({
        "checked":checked,
        "header_candidates":header_candidates,
        "decoded_records":len(rows),
        "samples":rows[:20],
    },indent=2))

if __name__=="__main__":
    main()
