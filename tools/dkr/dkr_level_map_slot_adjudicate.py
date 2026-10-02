from pathlib import Path
import argparse,json,collections
ap=argparse.ArgumentParser()
ap.add_argument("--join",required=True)
ap.add_argument("--entities",required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()
j=json.loads(Path(a.join).read_text())
e=json.loads(Path(a.entities).read_text())
maps={m["map_index"]:m for m in e["maps"]}
rows=[]
for r in j["rows"]:
 slot0=r["object_map_mode1"] # +0xBA, first call, a1=0
 slot1=r["object_map_mode0"] # +0x36, second call, a1=1
 def sm(mid):
  m=maps.get(mid)
  return {"map_index":mid,"state":m["state"] if m else "OUT_OF_RANGE","placement_count":m.get("placement_count",0) if m else 0}
 rows.append({
  "level_index":r["level_index"],"name_en":r["name_en"],"localized_names":r["localized_names"],
  "header_type_0x4C":r["header_type_0x4C"],
  "level_model_index":r["field_0x34"],
  "object_map_slot0":sm(slot0),
  "object_map_slot1":sm(slot1)
 })
report={
 "schema":"n64.dkr_level_object_map_slots.v1",
 "mechanics":{
  "slot0_header_offset":"0xBA","slot0_loader_a1":0,
  "slot1_header_offset":"0x36","slot1_loader_a1":1,
  "constructor_a1":"always 1 for both slots",
  "semantic_labels":"slot0/slot1; gameplay meaning not promoted beyond content characterization"
 },
 "levels":len(rows),
 "rows":rows
}
Path(a.out).write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({
 "levels":len(rows),
 "slot0_indices":[min(x["object_map_slot0"]["map_index"] for x in rows),max(x["object_map_slot0"]["map_index"] for x in rows)],
 "slot1_indices":[min(x["object_map_slot1"]["map_index"] for x in rows),max(x["object_map_slot1"]["map_index"] for x in rows)],
 "slot0_empty_levels":[x["name_en"] for x in rows if x["object_map_slot0"]["placement_count"]==0],
 "slot1_empty_levels":[x["name_en"] for x in rows if x["object_map_slot1"]["placement_count"]==0],
 "first20":[{"i":x["level_index"],"name":x["name_en"],"slot0":x["object_map_slot0"],"slot1":x["object_map_slot1"]} for x in rows[:20]]
},indent=2))
