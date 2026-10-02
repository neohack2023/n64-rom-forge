from pathlib import Path
import argparse, collections, json, struct, statistics

ap=argparse.ArgumentParser()
ap.add_argument("rzip_report")
ap.add_argument("--out",required=True)
a=ap.parse_args()
r=json.loads(Path(a.rzip_report).read_text(encoding="utf-8"))
banks=collections.defaultdict(list)
for row in r["rows"]:
    banks[row["path"].split("/")[0]].append(row)

def word(data,off):
    return struct.unpack_from(">I",data,off)[0] if off+4<=len(data) else None

out=[]
for bank,rows in sorted(banks.items()):
    samples=[]
    records=[]
    for row in rows:
        data=Path(row["decoded_path"]).read_bytes()
        records.append(data)
    max_scan=min(0x100,min(len(x) for x in records))
    fields=[]
    for off in range(0,max_scan,4):
        vals=[word(x,off) for x in records]
        ctr=collections.Counter(vals)
        plausible_rel=sum(1 for v,x in zip(vals,records) if v is not None and v%4==0 and 0 < v < len(x))
        small=sum(1 for v in vals if v is not None and v<=0x1000)
        fields.append({
            "offset":off,
            "top_values":[[f"0x{k:08X}",n] for k,n in ctr.most_common(6)],
            "distinct":len(ctr),
            "constant_fraction":round(ctr.most_common(1)[0][1]/len(vals),4),
            "relative_offset_fraction":round(plausible_rel/len(vals),4),
            "small_value_fraction":round(small/len(vals),4),
        })
    for row,data in zip(rows[:5],records[:5]):
        samples.append({
            "path":row["path"],"size":len(data),
            "words":[f"0x{word(data,o):08X}" for o in range(0,min(0x80,len(data)),4)]
        })
    out.append({
        "bank":bank,"records":len(records),
        "size_min":min(map(len,records)),
        "size_median":statistics.median(map(len,records)),
        "size_max":max(map(len,records)),
        "header_fields":fields,
        "samples":samples
    })
report={"schema":"n64.dkr_decoded_schema_profile.v1","banks":out}
Path(a.out).write_text(json.dumps(report,indent=2),encoding="utf-8")
brief=[]
for b in out:
    interesting=[f for f in b["header_fields"] if f["constant_fraction"]>=0.9 or f["relative_offset_fraction"]>=0.8]
    brief.append({"bank":b["bank"],"records":b["records"],"size_median":b["size_median"],"interesting_fields":interesting[:16],"sample0":b["samples"][0]})
print(json.dumps(brief,indent=2))
