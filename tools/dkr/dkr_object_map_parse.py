from pathlib import Path
import argparse,json,struct,statistics,collections

ap=argparse.ArgumentParser()
ap.add_argument("rzip_report")
ap.add_argument("--bank",default="pair_20_21")
ap.add_argument("--out",required=True)
a=ap.parse_args()
r=json.loads(Path(a.rzip_report).read_text(encoding="utf-8"))
rows=[x for x in r["rows"] if x["path"].split("/")[0]==a.bank]
parsed=[]
invalid=[]
ids=collections.Counter()
all_xyz=[]
for row in rows:
    data=Path(row["decoded_path"]).read_bytes()
    if len(data)<16:
        invalid.append({"path":row["path"],"reason":"short"})
        continue
    span=struct.unpack_from(">I",data,0)[0]
    pos=16; consumed=0; recs=[]
    reason=None
    while consumed<span:
        if pos+8>len(data):
            reason="record_header_oob"; break
        b0=data[pos]; b1=data[pos+1]; length=b1&0x3f
        if length<8:
            reason=f"invalid_record_length_{length}"; break
        if pos+length>len(data):
            reason="record_oob"; break
        obj_id=b0|((b1&0x80)<<1)
        x,y,z=struct.unpack_from(">hhh",data,pos+2)
        recs.append({"offset":pos,"length":length,"object_id":obj_id,"x":x,"y":y,"z":z})
        ids[obj_id]+=1; all_xyz.append((x,y,z))
        pos+=length; consumed+=length
    valid=(reason is None and consumed==span)
    item={"path":row["path"],"decoded_size":len(data),"record_span":span,"record_count":len(recs),"consumed":consumed,"valid":valid}
    if reason: item["reason"]=reason
    if recs: item["sample_records"]=recs[:5]
    (parsed if valid else invalid).append(item)

counts=[x["record_count"] for x in parsed]
report={
 "schema":"n64.dkr_object_map_parse.v1",
 "bank":a.bank,
 "input_records":len(rows),
 "valid_streams":len(parsed),
 "invalid_streams":len(invalid),
 "record_count_total":sum(counts),
 "record_count_min":min(counts) if counts else None,
 "record_count_median":statistics.median(counts) if counts else None,
 "record_count_max":max(counts) if counts else None,
 "unique_object_ids":len(ids),
 "top_object_ids":ids.most_common(32),
 "coordinate_ranges":{
   "x":[min(x[0] for x in all_xyz),max(x[0] for x in all_xyz)] if all_xyz else None,
   "y":[min(x[1] for x in all_xyz),max(x[1] for x in all_xyz)] if all_xyz else None,
   "z":[min(x[2] for x in all_xyz),max(x[2] for x in all_xyz)] if all_xyz else None
 },
 "streams":parsed,
 "invalid":invalid
}
Path(a.out).write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({k:v for k,v in report.items() if k not in ("streams","invalid")},indent=2))
print(json.dumps({"invalid":invalid[:10],"stream_samples":parsed[:5]},indent=2))
