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
for lev in j["rows"]:
 out={"level_index":lev["level_index"],"name":lev["name_en"],"header_type":lev["header_type_0x4C"]}
 for mode,key in [(0,"object_map_mode0"),(1,"object_map_mode1")]:
  mid=lev[key]
  m=maps.get(mid)
  cnt=collections.Counter(x["name"] or f'ID_{x["object_id"]}' for x in (m.get("placements",[]) if m else []))
  types=collections.Counter(x["behavior_type"] for x in (m.get("placements",[]) if m else []))
  out[f"mode{mode}"]={
   "map_index":mid,
   "state":m["state"] if m else "OUT_OF_RANGE",
   "placement_count":m.get("placement_count",0) if m else 0,
   "top_objects":cnt.most_common(15),
   "behavior_types":types.most_common(15)
  }
 rows.append(out)
report={"schema":"n64.dkr_level_object_map_layers.v1","rows":rows}
Path(a.out).write_text(json.dumps(report,indent=2),encoding="utf-8")
sel={0,1,3,5,12,21,24,25,37,40,47,55}
print(json.dumps([r for r in rows if r["level_index"] in sel],indent=2))
