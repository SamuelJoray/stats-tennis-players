# Shot codes: columns `1st` and `2nd` of table `points`

`1st` and `2nd` hold one point each, written as a string in the Match Charting Project
notation. Every shot is coded, including the serve. Read a code left to right:
serve → return → rally shots → how the point ended.

## Which column holds the point

- First serve **in**: the whole point (serve + rally + ending) is in `1st`. `2nd` is empty.
- First serve **fault**: `1st` holds only that serve (direction + fault type). The second serve
  and the rest of the point are in `2nd`.
- Double fault: `1st` and `2nd` each hold a faulted serve.

Examples:
- `1st = 6f27b1*`: serve down the T in, forehand return, backhand winner. `2nd` empty.
- `1st = 5d`, `2nd = 4s39b3b1w@`: first serve body, deep (fault); second serve wide in,
  then a rally ending in an unforced error wide.

## Who hit which shot

Shots alternate between the players: shot 1 = serve (server), shot 2 = return (returner),
shot 3 = server, shot 4 = returner, and so on. Odd-numbered shots are the server's,
even-numbered shots the returner's. The last shot's hitter won the point if it ends in `*`
(winner) and lost it if it ends in `@` or `#` (error). Lets (`c`) and the modifiers listed below
are not shots.
For who won the point, the `PtWinner` column is authoritative. Use the codes to know *how*.

## Serves

Serve direction (the same in the deuce and ad courts):
- `4` = out wide, `5` = body, `6` = down the T, `0` = unknown.

Fault types (lowercase, placed right after the direction):
- `n` = net (including net cords that are not lets)
- `w` = wide (either side)
- `d` = deep
- `x` = wide and deep
- `g` = foot fault
- `e` = fault of unknown type
- `!` = shanked serve (used instead of a fault letter)

Other serve codes:
- `c` = let, placed before the direction and repeated once per let (`cc4e` = two lets,
  then a wide serve that is a fault of unknown type).
- `+` right after the direction = serve-and-volley attempt, whether the serve went in or not
  (`4+w` = wide serve-and-volley attempt, fault wide).
- `V` (uppercase) = time violation costing the server his first serve (in `1st`).

Serve examples: `6` = T serve in; `4` = wide serve in; `6x` = T serve, fault wide and deep;
`5d` = body serve, fault deep.

## Points that end on the serve or the return

- Ace: serve + `*` (`5*` = body serve ace).
- Unreturnable: serve + `#` (`6#` = T serve the returner touched but could not return;
  includes returns not fully struck, shanked, not reaching the net, or wildly missed).
- Return forced error: serve + return shot + `#` (`6f#`).
- Return unforced error: serve + return shot + error type + `@` (`6f2d@`).

## Rally shots

Each shot after the serve is a shot-type letter followed by a direction digit.
Exceptions: the return has an extra depth digit, and the final error shot has extra codes
(see "How the point ended"). Direction and depth are optional, so they may be missing.

Shot types (forehand / backhand):
| Shot | Forehand | Backhand |
|---|---|---|
| Groundstroke (no slices or chips) | `f` | `b` |
| Slice (incl. defensive chips, not drop shots) | `r` | `s` |
| Volley | `v` | `z` |
| Overhead / smash | `o` | `p` |
| Drop shot | `u` | `y` |
| Lob | `l` | `m` |
| Half-volley | `h` | `i` |
| Swinging volley | `j` | `k` |

Also: `t` = trick shot (behind the back, tweener, etc.), `q` = unknown shot.

Direction (where the ball crossed, or would have crossed, the opponent's baseline):
- `1` = to a right-hander's forehand side (= a left-hander's backhand side)
- `2` = down the middle (roughly the central 40% of the court)
- `3` = to a right-hander's backhand side (= a left-hander's forehand side)
- `0` = unknown

Directions are relative to a right-handed *receiver*, not crosscourt / down the line.
Between two right-handers: `f1` = crosscourt forehand, `f3` = forehand down the line,
`b3` = crosscourt backhand, `b1` = backhand down the line. Swap for left-handers.

Return depth (third character of the return only, optional):
- `7` = lands inside the service boxes
- `8` = behind the service line, closer to the service line than the baseline
- `9` = closer to the baseline than the service line
- `0` = unknown depth
Example: `f37` = forehand return to a right-hander's backhand side, landing in the service box.

Rally examples:
- `b3s3b1f1v2` = backhand crosscourt, backhand slice crosscourt, backhand down the line,
  forehand crosscourt, volley down the middle (all right-handers).
- `fbh` = forehand, backhand, half-volley, without directions (valid).

## How the point ended

- Winner: last shot + `*` (`f3*` = forehand winner to a right-hander's backhand side).
- Error: the failed shot is included, then an error type and `@` or `#`:
  - error types: `n` = net, `w` = wide, `d` = deep, `x` = wide and deep, `!` = shank, `e` = unknown
  - `@` = unforced error, `#` = forced error
  - Full form: shot type, direction, error type, `@`/`#` (`f1n@`).
  - Unforced errors always have shot type + error type + `@`; direction is optional.
  - Forced errors may be only shot type + `#` (`b#`), or fuller (`b3d#`).

Full example: `5f2f1f1v2n@` = body serve in, forehand down the middle, forehand crosscourt,
forehand crosscourt, volley down the middle into the net, unforced error.

## Optional modifiers (placed right after the shot letter)

These are optional, so their absence does NOT mean the situation did not happen.
- `+` = approach shot (`b+2` = backhand approach down the middle). After a serve direction,
  `+` means serve-and-volley (`4+b27v1*`: wide serve, server rushes the net, short return
  down the middle, volley winner).
- `-` = shot hit at the net (for shots normally hit from the baseline): `f-1`.
- `=` = shot hit from the baseline (for shots normally hit at the net): `o=2`.
- `;` = ball clipped the net cord (`f;1*` = forehand winner that clipped the net).
- `^` = stop volley / drop volley (`z^2*` = backhand stop volley winner down the middle).

By default, volleys, half-volleys, swinging volleys and smashes are assumed to be at the net;
groundstrokes, slices, drop shots, lobs and trick shots from the baseline.

## Whole-point codes (uppercase, alone in `1st`)

- `S` = point not charted, awarded to the server
- `R` = point not charted, awarded to the returner
- `P` = point penalty against the server
- `Q` = point penalty against the returner

These rows have no shot information. Exclude them from shot-level statistics.

## Other codes

- `C` at the end of a rally = a player stopped play to challenge and was wrong
  (`6b29C` = T serve, backhand return deep down the middle, play stopped for an incorrect
  challenge). If the challenge was correct, the shot is coded as a normal error instead.
- Replayed points are not recorded; challenges that changed the result are already reflected.

## `Notes` column

Free text for anything not covered by the codes (challenges, medical timeouts, rain delays,
coaching, time-violation warnings). Usually empty. Events between points are noted on the
point *before* the event.

## Tips for SQL queries

- Characters that encode the outcome are at the END of the code: `*` winner,
  `#` forced error or unreturnable, `@` unforced error.
- Digits mean different things by position: `4`/`5`/`6` = serve direction (first shot only),
  `1`/`2`/`3` = rally direction, `7`/`8`/`9` = return depth.
- Use the column holding the point that was actually played: `2nd` if it is non-empty,
  otherwise `1st`, i.e. `COALESCE(NULLIF("2nd", ''), "1st")`.
- Quote the column names: `"1st"`, `"2nd"` (they start with a digit).
- Optional fields (direction, depth, modifiers) are missing in some charts, so results
  based on them only cover the points where they were recorded.
