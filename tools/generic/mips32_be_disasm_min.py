from pathlib import Path
import argparse,struct
R=["zero","at","v0","v1","a0","a1","a2","a3","t0","t1","t2","t3","t4","t5","t6","t7","s0","s1","s2","s3","s4","s5","s6","s7","t8","t9","k0","k1","gp","sp","fp","ra"]

def sx16(x): return x if x<0x8000 else x-0x10000
def dec(w,pc):
    op=(w>>26)&63; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31; sa=(w>>6)&31; fn=w&63; imm=w&0xffff
    if w==0: return "nop"
    if op==0:
        m={0:"sll",2:"srl",3:"sra",8:"jr",9:"jalr",33:"addu",35:"subu",36:"and",37:"or",38:"xor",42:"slt",43:"sltu"}.get(fn)
        if fn in (0,2,3): return f"{m} {R[rd]},{R[rt]},{sa}"
        if fn==8: return f"jr {R[rs]}"
        if fn==9: return f"jalr {R[rd]},{R[rs]}"
        if m: return f"{m} {R[rd]},{R[rs]},{R[rt]}"
    if op in (2,3):
        tgt=((pc+4)&0xF0000000)|((w&0x03ffffff)<<2)
        return f"{'j' if op==2 else 'jal'} 0x{tgt:08X}"
    if op in (4,5):
        tgt=(pc+4)+(sx16(imm)<<2)
        return f"{'beq' if op==4 else 'bne'} {R[rs]},{R[rt]},0x{tgt:08X}"
    if op in (6,7):
        tgt=(pc+4)+(sx16(imm)<<2)
        return f"{'blez' if op==6 else 'bgtz'} {R[rs]},0x{tgt:08X}"
    names={8:"addi",9:"addiu",10:"slti",11:"sltiu",12:"andi",13:"ori",14:"xori"}
    if op in names:
        val=imm if op in (12,13,14) else sx16(imm)
        return f"{names[op]} {R[rt]},{R[rs]},{val if val<10 else hex(val & 0xffff if op in (12,13,14) else val)}"
    if op==15: return f"lui {R[rt]},0x{imm:04X}"
    mem={32:"lb",33:"lh",35:"lw",36:"lbu",37:"lhu",40:"sb",41:"sh",43:"sw"}.get(op)
    if mem: return f"{mem} {R[rt]},{sx16(imm)}({R[rs]})"
    if op==1:
        tgt=(pc+4)+(sx16(imm)<<2)
        return f"regimm rt={rt} {R[rs]},0x{tgt:08X}"
    if op in (16,17,18,19): return f"cop{op-16} 0x{w&0x03ffffff:07X}"
    return f".word 0x{w:08X}"
ap=argparse.ArgumentParser()
ap.add_argument("rom")
ap.add_argument("start",type=lambda x:int(x,0))
ap.add_argument("count",type=int)
ap.add_argument("--rom-base",type=lambda x:int(x,0),default=0x1000)
ap.add_argument("--vram-base",type=lambda x:int(x,0),default=0x80000400)
a=ap.parse_args()
data=Path(a.rom).read_bytes()
off=a.rom_base+(a.start-a.vram_base)
for i in range(a.count):
    o=off+i*4; pc=a.start+i*4
    if o<0 or o+4>len(data): break
    w=struct.unpack_from(">I",data,o)[0]
    print(f"{pc:08X}  {w:08X}  {dec(w,pc)}")
