from pathlib import Path
import argparse,json,struct,re,collections
ap=argparse.ArgumentParser()
ap.add_argument("--nested-report",required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()
n=json.loads(Path(a.nested_report).read_text())
hp=[p for p in n["pairs"] if p["table_section"]==22 and p["payload_section"]==23][0]
np=[p for p in n["pairs"] if p["table_section"]==24 and p["payload_section"]==25][0]

def cstrings(data):
 out=[]; cur=[]
 for b in data:
  if b==0:
   if cur:
    try:
     s=bytes(cur).decode("ascii")
     if s and all(32<=ord(ch)<127 for ch in s): out.append(s)
    except: pass
   cur=[]
  else: cur.append(b)
 if cur:
  try: out.append(bytes(cur).decode("ascii"))
  except: pass
 return out

rows=[]
for i,item in enumerate(hp["items"]):
 data=Path(item["dump"]).read_bytes()
 names=cstrings(Path(np["items"][i]["dump"]).read_bytes()) if i<len(np["items"]) else []
 def s16(o): return struct.unpack_from(">h",data,o)[0] if o+2<=len(data) else None
 def u8(o): return data[o] if o<len(data) else None
 rows.append({
  "level_index":i,
  "name_en":names[0] if names else None,
  "localized_names":names,
  "header_size":len(data),
  "header_type_0x4C":struct.unpack("b",data[0x4c:0x4d])[0] if len(data)>0x4c else None,
  "field_0x34":s16(0x34),
  "object_map_mode0":s16(0x36),
  "field_0x38":s16(0x38),
  "object_map_mode1":s16(0xba),
  "field_0xB0":s16(0xb0),
  "byte_0x4D":u8(0x4d),
  "byte_0x4E":u8(0x4e)
 })
report={
 "schema":"n64.dkr_level_header_object_map_join.v1",
 "header_pair":"22->23",
 "name_pair":"24->25",
 "header_slots":hp["item_count"],
 "name_slots":np["item_count"],
 "rows":rows
}
Path(a.out).write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({
 "header_slots":report["header_slots"],"name_slots":report["name_slots"],
 "header_sizes":collections.Counter(r["header_size"] for r in rows),
 "rows":rows
},indent=2,default=list))
