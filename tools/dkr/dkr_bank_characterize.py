from pathlib import Path
import argparse, collections, json, re, statistics

def semantic_strings(data, limit=12):
    out=[]
    for m in re.finditer(rb"[A-Za-z][A-Za-z0-9 _.'!?:/-]{5,79}", data):
        text=m.group().decode("ascii","replace").strip()
        alpha=sum(c.isalpha() for c in text)
        if alpha / max(1,len(text)) < 0.65:
            continue
        if len(set(text.lower())) < 4:
            continue
        out.append({"offset":m.start(),"text":text})
        if len(out)>=limit:
            break
    return out

def median(values):
    return statistics.median(values) if values else None

ap=argparse.ArgumentParser()
ap.add_argument("--nested-report",required=True)
ap.add_argument("--rzip-report",required=True)
ap.add_argument("--nested-root",required=True)
ap.add_argument("--decoded-root",required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()

nested=json.loads(Path(a.nested_report).read_text(encoding="utf-8"))
rzip=json.loads(Path(a.rzip_report).read_text(encoding="utf-8"))
by_pair=collections.defaultdict(lambda:{
    "items":0,"rzip":0,"raw_sizes":[],"decoded_sizes":[],
    "decoded_prefix4":collections.Counter(),"semantic_strings":[]
})
for pair in nested["pairs"]:
    key=f'pair_{pair["table_section"]:02d}_{pair["payload_section"]:02d}'
    x=by_pair[key]
    x["items"]=pair["item_count"]
    x["raw_sizes"]=[item["size"] for item in pair["items"]]
    for item in pair["items"]:
        if len(x["semantic_strings"])>=12:
            break
        data=Path(item["dump"]).read_bytes()
        for s in semantic_strings(data,4):
            if s["text"] not in [z["text"] for z in x["semantic_strings"]]:
                x["semantic_strings"].append({"source":"raw","item":item["index"],**s})
                if len(x["semantic_strings"])>=12:
                    break

decoded_root=Path(a.decoded_root)
for row in rzip["rows"]:
    key=row["path"].split("/")[0]
    x=by_pair[key]
    x["rzip"]+=1
    x["decoded_sizes"].append(row["decoded_size"])
    decoded=Path(row["decoded_path"]).read_bytes()
    x["decoded_prefix4"][decoded[:4].hex()]+=1
    if len(x["semantic_strings"])<12:
        for s in semantic_strings(decoded,4):
            if s["text"] not in [z["text"] for z in x["semantic_strings"]]:
                x["semantic_strings"].append({"source":"decoded","item":row["path"],**s})
                if len(x["semantic_strings"])>=12:
                    break

rows=[]
for key,x in sorted(by_pair.items()):
    rows.append({
        "pair":key,
        "items":x["items"],
        "rzip_records":x["rzip"],
        "rzip_fraction":round(x["rzip"]/max(1,x["items"]),4),
        "raw_size_min":min(x["raw_sizes"]) if x["raw_sizes"] else None,
        "raw_size_median":median(x["raw_sizes"]),
        "raw_size_max":max(x["raw_sizes"]) if x["raw_sizes"] else None,
        "decoded_size_min":min(x["decoded_sizes"]) if x["decoded_sizes"] else None,
        "decoded_size_median":median(x["decoded_sizes"]),
        "decoded_size_max":max(x["decoded_sizes"]) if x["decoded_sizes"] else None,
        "common_decoded_prefix4":x["decoded_prefix4"].most_common(8),
        "semantic_string_samples":x["semantic_strings"],
    })

report={"schema":"n64.dkr_bank_characterization.v1","banks":rows}
Path(a.out).write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"banks":[{
    "pair":x["pair"],"items":x["items"],"rzip_fraction":x["rzip_fraction"],
    "decoded_median":x["decoded_size_median"],
    "strings":[s["text"] for s in x["semantic_string_samples"][:4]]
} for x in rows]},indent=2))
