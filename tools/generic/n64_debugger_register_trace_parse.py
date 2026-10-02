from pathlib import Path
import argparse,json,re

ap=argparse.ArgumentParser()
ap.add_argument("log")
ap.add_argument("--pc",required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()
text=Path(a.log).read_text(encoding="utf-8",errors="replace")
text=re.sub(r"\x1b\[[0-9;]*m","",text)
pc=a.pc.lower().replace("0x","")
blocks=text.split("General Purpose Registers:")
hits=[]
for block in blocks[1:]:
    pre=block[:400]
    mpc=re.search(r"PC:\s*([0-9A-Fa-f]+)",pre)
    if not mpc:
        before=blocks[0] if not hits else ""
    regs={}
    for name in ("a0","a1","a2","a3","v0","v1","t0","t1","t2","t3","t4","t5","t6","t7","t8","t9","s0","s1","s2","s3","s4","s5","s6","s7","sp","ra"):
        m=re.search(rf"(?:\$)?{name}\s+([0-9A-Fa-f]+)",block[:2200],re.I)
        if m:
            regs[name]="0x"+m.group(1).upper()
    hits.append(regs)
summary={
  "schema":"n64.debugger_register_trace.v1",
  "target_pc":"0x"+pc.upper(),
  "hit_count":len(hits),
  "hits":hits,
  "a0_values":[h.get("a0") for h in hits],
  "unique_a0":sorted(set(h.get("a0") for h in hits if h.get("a0"))),
  "unique_ra":sorted(set(h.get("ra") for h in hits if h.get("ra")))
}
Path(a.out).write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
