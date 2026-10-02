from pathlib import Path
import argparse,json,collections

ap=argparse.ArgumentParser()
ap.add_argument("--entities",required=True)
ap.add_argument("--nested-report",required=True)
ap.add_argument("--rzip-report",required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()
entities=json.loads(Path(a.entities).read_text())
nested=json.loads(Path(a.nested_report).read_text())
rzip=json.loads(Path(a.rzip_report).read_text())

pair=[p for p in nested["pairs"] if p["table_section"]==28 and p["payload_section"]==29][0]
model_items={x["index"]:x for x in pair["items"]}
rzip_models={}
for row in rzip["rows"]:
    if row["path"].startswith("pair_28_29/"):
        idx=int(Path(row["path"]).name.split("_")[1])
        rzip_models[idx]=row

refs=collections.Counter()
owners=collections.defaultdict(set)
for m in entities["maps"]:
    for e in m.get("placements",[]):
        for mid in e["model_ids"]:
            refs[mid]+=1
            owners[mid].add((e["object_id"],e["name"]))

rows=[]
missing=[]
for mid,count in sorted(refs.items()):
    item=model_items.get(mid)
    rz=rzip_models.get(mid)
    if item is None or rz is None:
        missing.append({"model_id":mid,"references":count,"has_item":item is not None,"has_rzip":rz is not None})
        continue
    rows.append({
      "model_id":mid,
      "references":count,
      "owners":[{"object_id":oid,"name":name} for oid,name in sorted(owners[mid])],
      "compressed_size":item["size"],
      "decoded_size":rz["decoded_size"],
      "decoded_sha256":rz["decoded_sha256"],
      "decoded_prefix32":rz["decoded_prefix32"]
    })
report={
 "schema":"n64.dkr_object_model_resolution.v1",
 "object_model_slots":pair["item_count"],
 "unique_referenced_model_ids":len(refs),
 "resolved_model_ids":len(rows),
 "missing_model_ids":missing,
 "rows":rows
}
Path(a.out).write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({
 "object_model_slots":report["object_model_slots"],
 "unique_referenced_model_ids":report["unique_referenced_model_ids"],
 "resolved_model_ids":report["resolved_model_ids"],
 "missing_model_ids":missing,
 "samples":rows[:20]
},indent=2))
