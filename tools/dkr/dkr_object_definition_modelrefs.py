from pathlib import Path
import argparse,json,struct

ap=argparse.ArgumentParser()
ap.add_argument("--crossindex",required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()
x=json.loads(Path(a.crossindex).read_text())
rows=[]
for r in x["rows"]:
    data=Path(r["definition_path"]).read_bytes()
    def u32(off):
        return struct.unpack_from(">I",data,off)[0] if off+4<=len(data) else None
    def u8(off):
        return data[off] if off<len(data) else None
    ptrs={f"0x{off:02X}":u32(off) for off in (0x10,0x14,0x18,0x1C,0x24)}
    target=ptrs["0x10"]
    model_words=[]
    if target is not None and 0 <= target < len(data):
        for off in range(target,min(target+0x40,len(data)),4):
            model_words.append({"offset":off,"u32":u32(off),"hex":f"0x{u32(off):08X}"})
    name=None
    if len(data)>0x60:
        raw=data[0x60:]
        end=raw.find(b"\x00")
        if end<0: end=min(len(raw),64)
        try:
            t=raw[:end].decode("ascii")
            if t and all(32<=ord(ch)<127 for ch in t): name=t
        except: pass
    rows.append({
      "object_id":r["object_id"],
      "placements":r["placements"],
      "name":name,
      "definition_size":len(data),
      "type_bytes":{"0x52":u8(0x52),"0x53":u8(0x53),"0x54":u8(0x54),"0x55":u8(0x55)},
      "relative_pointers":ptrs,
      "model_array_words":model_words
    })
report={"schema":"n64.dkr_object_definition_modelrefs.v1","rows":rows}
Path(a.out).write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({
 "rows":len(rows),
 "samples":[r for r in rows if r["object_id"] in (5,18,20,24,35,49,83,148,265)]
},indent=2))
