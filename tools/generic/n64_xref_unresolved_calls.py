from pathlib import Path
import argparse,json
ap=argparse.ArgumentParser()
ap.add_argument("report")
a=ap.parse_args()
d=json.loads(Path(a.report).read_text(encoding="utf-8"))
rows=[]
for x in d["hits"]:
    if x.get("nearest_a0_constant") is None:
        rows.append({
            "call_vram":f'0x{x["call_vram"]:08X}',
            "return_vram":f'0x{x["return_vram"]:08X}',
            "delay_slot":x.get("delay_slot"),
            "context":x.get("context",[]),
        })
print(json.dumps({"count":len(rows),"rows":rows},indent=2))
