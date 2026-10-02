from pathlib import Path
import argparse, collections, json

ap=argparse.ArgumentParser()
ap.add_argument("report")
ap.add_argument("--out", required=True)
a=ap.parse_args()
d=json.loads(Path(a.report).read_text(encoding="utf-8"))
by_pair=collections.defaultdict(lambda: {"decoded":0,"compressed_bytes":0,"decoded_bytes":0,"min_ratio":None,"max_ratio":None})
for row in d["rows"]:
    pair=row["path"].split("/")[0]
    x=by_pair[pair]
    x["decoded"]+=1
    x["compressed_bytes"]+=row["compressed_size"]
    x["decoded_bytes"]+=row["decoded_size"]
    ratio=row["ratio"]
    x["min_ratio"]=ratio if x["min_ratio"] is None else min(x["min_ratio"],ratio)
    x["max_ratio"]=ratio if x["max_ratio"] is None else max(x["max_ratio"],ratio)
summary={
    "schema":"n64.dkr_rzip_summary.v1",
    "checked":d["checked"],
    "header_candidates":d["header_candidates"],
    "decoded_records":d["decoded_records"],
    "failed_header_candidates":d["header_candidates"]-d["decoded_records"],
    "by_pair":dict(sorted(by_pair.items())),
}
Path(a.out).write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
