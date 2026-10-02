from pathlib import Path
import argparse,json,re,struct,collections,statistics

ap=argparse.ArgumentParser()
ap.add_argument("--map-report",required=True)
ap.add_argument("--nested-report",required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()
maps=json.loads(Path(a.map_report).read_text())
nested=json.loads(Path(a.nested_report).read_text())
pair=[p for p in nested["pairs"] if p["table_section"]==33 and p["payload_section"]==34][0]
defs={x["index"]:x for x in pair["items"]}

used=collections.Counter()
for s in maps["streams"]:
    for r in s.get("sample_records",[]):
        pass
# exact counts come from top_object_ids only partially, so rescan parsed decoded maps
rzip_root=Path(maps["streams"][0]["path"]).parent if False else None

# use top_object_ids + full map parse source rows are summarized, so recover IDs from decoded files referenced by map report paths
map_report_path=Path(a.map_report)
base=map_report_path.parents[1]/"derived"/"DKR_US_REVA"/"rzip_decoded"
for s in maps["streams"]:
    # derive decoded filename convention from path
    rel=s["path"].replace("/","__")+".decoded.bin"
    f=base/rel
    if not f.exists():
        continue
    data=f.read_bytes()
    span=struct.unpack_from(">I",data,0)[0]
    pos=16; consumed=0
    while consumed<span:
        b0,b1=data[pos],data[pos+1]
        ln=b1&0x3f
        oid=b0|((b1&0x80)<<1)
        used[oid]+=1
        pos+=ln; consumed+=ln

def strings(data,limit=8):
    out=[]
    for m in re.finditer(rb"[A-Za-z][A-Za-z0-9_ ./-]{3,63}",data):
        t=m.group().decode("ascii","replace").strip()
        if sum(ch.isalpha() for ch in t)>=3:
            out.append({"offset":m.start(),"text":t})
            if len(out)>=limit: break
    return out

rows=[]
missing=[]
for oid,count in sorted(used.items()):
    item=defs.get(oid)
    if not item:
        missing.append({"object_id":oid,"placements":count})
        continue
    data=Path(item["dump"]).read_bytes()
    u32=[struct.unpack_from(">I",data,o)[0] for o in range(0,min(len(data),0x80)-3,4)]
    s16=[struct.unpack_from(">h",data,o)[0] for o in range(0,min(len(data),0x80)-1,2)]
    rows.append({
      "object_id":oid,
      "placements":count,
      "definition_size":len(data),
      "definition_path":item["dump"],
      "prefix64":data[:64].hex(),
      "strings":strings(data),
      "u32_head":[f"0x{x:08X}" for x in u32[:24]],
      "s16_head":s16[:32]
    })
report={
 "schema":"n64.dkr_object_definition_crossindex.v1",
 "definition_slots":pair["item_count"],
 "used_object_ids":len(used),
 "mapped_definition_ids":len(rows),
 "missing_definition_ids":missing,
 "rows":rows
}
Path(a.out).write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({
 "definition_slots":report["definition_slots"],
 "used_object_ids":report["used_object_ids"],
 "mapped_definition_ids":report["mapped_definition_ids"],
 "missing_definition_ids":missing,
 "size_distribution":collections.Counter(r["definition_size"] for r in rows).most_common(20),
 "string_hits":[{"id":r["object_id"],"placements":r["placements"],"strings":r["strings"]} for r in rows if r["strings"]][:30]
},indent=2))
