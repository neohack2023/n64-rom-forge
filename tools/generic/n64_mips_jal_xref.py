from pathlib import Path
import argparse,json,struct

ap=argparse.ArgumentParser()
ap.add_argument("rom")
ap.add_argument("--target",required=True,type=lambda x:int(x,0))
ap.add_argument("--rom-base",type=lambda x:int(x,0),default=0x1000)
ap.add_argument("--vram-base",type=lambda x:int(x,0),default=0x80000400)
ap.add_argument("--lookback",type=int,default=8)
ap.add_argument("--out",required=True)
a=ap.parse_args()

data=Path(a.rom).read_bytes()
jal=0x0C000000 | ((a.target>>2)&0x03FFFFFF)
sig=struct.pack(">I",jal)

def decode_li_a0(word):
    op=(word>>26)&0x3f
    rs=(word>>21)&0x1f
    rt=(word>>16)&0x1f
    imm=word&0xffff
    simm=imm if imm<0x8000 else imm-0x10000
    if rt!=4: return None
    if op==0x09 and rs==0: return {"kind":"addiu","value":simm}
    if op==0x0D and rs==0: return {"kind":"ori","value":imm}
    return None

hits=[]
pos=0
while True:
    off=data.find(sig,pos)
    if off<0: break
    if off%4:
        pos=off+1
        continue
    vram=a.vram_base+(off-a.rom_base)
    prev=[]
    const=None
    for n in range(a.lookback,0,-1):
        poff=off-n*4
        if poff<a.rom_base: continue
        w=struct.unpack_from(">I",data,poff)[0]
        row={"rom_offset":poff,"vram":a.vram_base+(poff-a.rom_base),"word":f"0x{w:08X}"}
        li=decode_li_a0(w)
        if li:
            row["a0_constant"]=li
            const=li["value"]
        prev.append(row)
    delay_off=off+4
    delay_word=struct.unpack_from(">I",data,delay_off)[0] if delay_off+4<=len(data) else None
    delay_row=None
    if delay_word is not None:
        delay_row={"rom_offset":delay_off,"vram":a.vram_base+(delay_off-a.rom_base),"word":f"0x{delay_word:08X}"}
        delay_li=decode_li_a0(delay_word)
        if delay_li:
            delay_row["a0_constant"]=delay_li
            const=delay_li["value"]
    hits.append({
        "call_rom_offset":off,
        "call_vram":vram,
        "return_vram":vram+8,
        "jal_word":f"0x{jal:08X}",
        "nearest_a0_constant":const,
        "delay_slot":delay_row,
        "context":prev
    })
    pos=off+4
report={"schema":"n64.mips_jal_xref.v1","target":f"0x{a.target:08X}","hit_count":len(hits),"hits":hits}
Path(a.out).write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({
    "target":report["target"],"hit_count":len(hits),
    "constant_calls":[{"call_vram":f'0x{x["call_vram"]:08X}',"return_vram":f'0x{x["return_vram"]:08X}',"a0":x["nearest_a0_constant"]} for x in hits if x["nearest_a0_constant"] is not None]
},indent=2))
