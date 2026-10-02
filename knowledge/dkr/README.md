# Diddy Kong Racing US Rev A knowledge

Canonical local research target:
- title: Diddy Kong Racing (USA) (En,Fr) (Rev A)
- size: 12,582,912 bytes
- SHA-1: `6d96743d46f8c0cd0edb0ec5600b003c89b93755`
- SHA-256: `7de1a8fb2a9558cfc3d9ad4497df698c1e89cf7095ac1531557df2af40ba8bcf`
- MD5: `b31f8cca50f31acc9b999ed5b779d6ed`
- internal name: `Diddy Kong Racing`
- game code: `NDYE`
- version: 1

Validated local findings:
- top-level asset LUT at ROM offset `0xED0E0`
- 50 top-level asset sections, payload base `0xED1B0`
- DKR compressed wrapper: LE decoded-size u32, byte `0x09`, raw DEFLATE, zero padding
- 1,052 fully valid nested DKR RZIP decodes across the characterized banks
- level models: pair 26 -> 27
- object models: pair 28 -> 29
- animation IDs: section 30
- object animations: pair 31 -> 32
- object definitions: pair 33 -> 34
- sections 20 -> 21: 138 object-map slots, 136 compressed non-empty maps, empty slots 81 and 99
- 9,426 parsed object-placement records across 136 maps
- object placement IDs index directly into section-33 object-definition offsets
- 85 level-used object IDs map to 304 object-definition slots with no missing references
- 177 distinct referenced object-model IDs resolve into pair 28 -> 29 with no missing references
- level metadata uses +0xBA for object-map slot 0 and +0x36 for slot 1
- native level selector: `0x8006B490`
- general runtime object constructor: `0x8000EA54`

Validated direct-level experiment:
- target: Ancient Lake, level index 5
- native selector received level 5
- downstream map loader selected map 5 in slot 0 and map 73 in slot 1
- redirect changed only the saved level argument before the game's native transition path

Not yet promoted:
- generalized named-level launcher
- semantic name for transition argument `a1`
- semantic names for the remaining transition tuple
- full object behavior-type names and placement-parameter schemas

The unfinished generalized launcher is intentionally not committed as a working tool.
