# Mupen64Plus Debug Runtime

This repo does not commit generated third-party emulator binaries. It records the exact source pins, debugger patch, Windows build recipe, tested launch contract, and hashes of the Host02 runtime that produced valid debugger evidence.

Validated source pins:
- core: `b0d68c20f49b8f833afa21450e0e8874c87c13c4`
- UI console: `1a68327fddda71f1acbad8a63ef04288b1887d19`

Validated launch mode:
`--debug --emumode 1`

Validated plugins:
- Rice video
- SDL input
- HLE RSP
- dummy audio for headless/debug probes

The timed probe runner was used successfully for breakpoint/register traces and DKR's bounded Ancient Lake direct-level transition.

Do not treat a queued debugger command as evidence unless the intended breakpoint actually fired. MIPS branch-delay slots must be modeled when interpreting callsite constants.
