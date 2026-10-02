from pathlib import Path
import argparse,json,struct,collections,statistics

ap=argparse.ArgumentParser()
ap.add_argument("--rzip-report",required=True)
ap.add_argument("--defs-report",required=True)
ap.add_argument("--nested-report",required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()

rzip=json.loads(Path(a.rzip_report).read_text())
defs=json.loads(Path(a.defs_report).read_text())
nested=json.loads(Path(a.nested_report).read_text())
defmap={r["object_id"]:r for r in defs["rows"]}

pair=[p for p in nested["pairs"] if p["table_section"]==20 and p["payload_section"]==21][0]
slot_count=pair["item_count"]
rzip_by_slot={}
for row in rzip["rows"]:
    if not row["path"].startswith("pair_20_21/"):
        continue
    name=Path(row["path"]).name
    slot=int(name.split("_")[1])
    rzip_by_slot[slot]=row

maps=[]
placement_total=0
name_counts=collections.Counter()
type_counts=collections.Counter()
model_counts=collections.Counter()

for slot in range(slot_count):
    row=rzip_by_slot.get(slot)
    if row is None:
        maps.append({"map_index":slot,"state":"EMPTY","placements":[]})
        continue
    data=Path(row["decoded_path"]).read_bytes()
    span=struct.unpack_from(">I",data,0)[0]
    pos=16; consumed=0; placements=[]
    while consumed<span:
        b0,b1=data[pos],data[pos+1]
        ln=b1&0x3f
        oid=b0|((b1&0x80)<<1)
        x,y,z=struct.unpack_from(">hhh",data,pos+2)
        dr=defmap[oid]
        model_ids=[w["u32"] for w in dr["model_array_words"][:dr["type_bytes"]["0x55"]]]
        ent={
          "object_id":oid,
          "name":dr["name"],
          "behavior_type":dr["type_bytes"]["0x54"],
          "model_count":dr["type_bytes"]["0x55"],
          "model_ids":model_ids,
          "record_offset":pos,
          "record_length":ln,
          "x":x,"y":y,"z":z
        }
        placements.append(ent)
        placement_total+=1
        name_counts[dr["name"] or f"ID_{oid}"]+=1
        type_counts[dr["type_bytes"]["0x54"]]+=1
        for mid in model_ids: model_counts[mid]+=1
        pos+=ln; consumed+=ln
    maps.append({
      "map_index":slot,
      "state":"PARSED",
      "record_span":span,
      "placement_count":len(placements),
      "placements":placements
    })

report={
 "schema":"n64.dkr_level_object_entities.v1",
 "map_slots":slot_count,
 "parsed_maps":sum(1 for m in maps if m["state"]=="PARSED"),
 "empty_maps":[m["map_index"] for m in maps if m["state"]=="EMPTY"],
 "placements":placement_total,
 "unique_names":len(name_counts),
 "unique_behavior_types":len(type_counts),
 "unique_model_ids":len(model_counts),
 "top_names":name_counts.most_common(40),
 "behavior_type_counts":sorted(type_counts.items()),
 "top_model_ids":model_counts.most_common(40),
 "maps":maps
}
Path(a.out).write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({k:v for k,v in report.items() if k!="maps"},indent=2))
