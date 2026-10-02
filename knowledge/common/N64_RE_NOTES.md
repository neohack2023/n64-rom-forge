# Common N64 reverse-engineering notes

These are reusable rules that survived work across multiple local ROMs.

## Identity first

Pin exact ROM revision, byte order, size, and hashes before assigning semantics. `.z64`, `.v64`, and `.n64` are representations, not interchangeable evidence unless normalization is explicit.

## MIPS call analysis

N64 code is MIPS with branch delay slots. For a `jal`, the instruction immediately after the call executes before control transfers. Constant propagation that ignores that delay slot can assign the wrong call argument.

## Resource discovery

Do not assume every game uses the same asset-table shape. DKR disproved a reusable Rugrats-style absolute start/end-table hypothesis and instead used a top-level relative LUT with nested adjacent LUT/payload banks.

Compression probes must require strong invariants. Arbitrary binary can accidentally terminate as a tiny raw-DEFLATE stream; wrapper magic, declared-size agreement, EOF, and padding constraints turn that into useful evidence.

## Runtime evidence

A debugger command sequence is not proof by itself. Record the intended breakpoint, verify it actually fired, capture registers/memory after the hit, and classify timing failures as invalid probes rather than ROM hypothesis failures.

## Portability

Keep generic tools parameterized. ROM-specific labels and addresses belong in adapters or knowledge packages, not in generic analyzers.
