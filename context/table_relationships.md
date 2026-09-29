# Tables and relationships

## Core tables
- matches: one row per match. Key: match_id.
  **Not strictly unique** -- a small number of match_ids appear twice (e.g. one Davis Cup
  match logged twice). If you need an exact match count, decide whether you want raw
  `COUNT(*)` or `COUNT(DISTINCT match_id)` -- they differ by a handful of rows.
- points: one row per point. Key: (match_id, Pt).
- stats_overview: one row per player **per set**, not one row per player. Key:
  (match_id, player, set), set ∈ {'1','2','3','4','5','Total'}. So up to 12 rows per match
  (2 players x up to 6 set rows), not 2.  <!-- resolved: verified with GROUP BY set -->
  Also **not strictly unique**: a handful of (match_id, player, set) combos have duplicate
  rows, same root cause as the matches duplicates above.

Relationships:
- matches 1 → N points (on match_id): about 100–300 points per match.
- matches 1 → N stats_overview (on match_id): up to 12 rows per match (see above), not 2.
- matches 1 → N of every stats_* table below (on match_id) -- same caution applies to all.

## stats_* tables (one per match report category, 16 total)

All 16 share the same shape: `match_id`, a player identifier (`player`, or `server`+`returner`
for stats_rally), a breakdown column (usually `row`, sometimes `set`), a set of numeric count
columns, and `tour`. **Watch for two different double-counting traps:**
1. Most breakdown columns include an aggregate value (often `'Total'`, sometimes
   `'STotal'`/`'RTotal'`, sometimes none at all) that already sums the other rows for that
   player/match. Filter to just the aggregate for a match total, or exclude it before summing
   the individual categories -- never both.
2. Several tables also nest categories inside each other (e.g. a serve-direction row like `'4'`
   already includes the court-side split `'4a'`+`'4d'`). Summing a parent row together with its
   children double-counts. See the table below for which ones do this.

| table | breakdown column | values (verified) | meaning |
|---|---|---|---|
| stats_servebasics | row | '1', '2', 'Total' | 1st serve / 2nd serve / both (flat, no nesting) |
| stats_servedirection | row | '1', '2', 'Total' | 1st serve / 2nd serve / both (flat, no nesting) |
| stats_serveinfluence | row | 1, 2 | 1st serve / 2nd serve -- **no Total row at all** in this table |
| stats_svbreaktotal | row | 4, 4a, 4d, 5, 5a, 5d, 6, 6a, 6d, a, d | serve direction (4/5/6 = wide/body/T, same digits as the points notation in context/points.md) x court side (a = ad court, d = deuce court). **Nested**: '4' already equals '4a'+'4d'. No flat 'Total' row -- for a grand total sum '4'+'5'+'6' (or 'a'+'d'), not all 11 rows. |
| stats_svbreaksplit | row | same value set as svbreaktotal | same shape and nesting caveat as stats_svbreaktotal |
| stats_returndepth | row | 4,4A,4D,5,5A,5D,6,6A,6D,A,D,'Total','bh','fh','gs','sl','v1st','v2nd' | **DANGER -- two independent, overlapping breakdowns share this one column.** Digits+letters (4,4A,4D,5,5A,5D,6,6A,6D,A,D) are serve direction x court side, nested exactly like stats_svbreaktotal ('4' = '4A'+'4D'; 'A' = the ad-court share of every direction). Separately, bh/fh/gs/sl/v1st/v2nd is a *different* breakdown, by the returner's shot type -- these are NOT additional siblings of the direction rows, they re-describe the *same underlying returns* from a different angle. **For any match/player total, use only `row = 'Total'`. Never filter `row != 'Total'` and sum what's left** -- that sums both breakdowns together and double-, triple-, or worse-counts. Cookbook query for a clean total: `SELECT deep, very_deep, shallow FROM stats_returndepth WHERE match_id = ? AND player = ? AND row = 'Total'`. |
| stats_returnoutcomes | row | same as returndepth plus '7','8','9','89' | same DANGER as stats_returndepth -- same two overlapping breakdowns, plus 7/8/9/'89' (return-depth codes from context/points.md: 7 = within service box, 8 = mid-court, 9 = closer to baseline) as a *third* overlapping dimension. **Use only `row = 'Total'` for any total; do not sum any subset of the other rows.** |
| stats_shottypes | row | e.g. 'Gs','Sl','Ov','H','V','B','Net',... | shot-type categories (groundstroke, slice, overhead, half-volley, volley, backhand, net-related); no confirmed aggregate row seen -- verify before assuming rows sum to a match total |
| stats_shotdirection | row | 'B','F','S','Total' | Backhand / Forehand / Slice, plus a flat 'Total' (no nesting) |
| stats_shotdiroutcomes | row | e.g. 'F-DTL','F-XC','F-IO','F-II','F-DTM', same for B- and S- prefixes | shot-type (F/B/S) x direction (DTL = down the line, XC = crosscourt, IO = inside-out, II = inside-in, DTM = down the middle). No aggregate row seen -- sum across all codes for a player total. |
| stats_snv | row | SnV1st, SnV2nd, SnV, nonSnV1st, nonSnV2nd, nonSnV | serve-and-volley vs not, split by serve number; 'SnV'/'nonSnV' appear to be the 1st+2nd combined totals for each group -- treat as nested, same caution as svbreaktotal |
| stats_netpoints | row | Approach, NetPoints, ApproachRallies, NetPointsRallies | four different net-point definitions, **not** mutually exclusive categories to sum -- pick the one row that matches the question instead |
| stats_keypointsserve | row | Deuce, STotal, BP, GP | serving stats at deuce points / break points / game points, plus 'STotal' (overall). These overlap (a break point can also be a deuce point) -- don't sum them, they aren't disjoint. |
| stats_keypointsreturn | row | DeuceR, RTotal, BPO, GPF | same idea as keypointsserve, for returning; overlapping categories, don't sum |
| stats_rally | server, returner, row | '1-3','1-3-1','1-3-2','4-6','4-6-1','4-6-2','7-9','7-9-1','7-9-2','10','10-1','10-2','Total' | **verified**: row is a rally-length bucket (e.g. '1-3' = rallies of 1-3 shots, '10' = 10+ shots), and the base buckets ('1-3','4-6','7-9','10') already sum to 'Total'. The `-1`/`-2` suffix splits each base bucket by which original match player (Player 1 vs Player 2) was serving -- and `server`/`returner` swap accordingly on those sub-rows. Crucially, `pl1_won`/`pl2_won` always mean Player 1/Player 2 (as in the `matches` table), **not** "whoever is server/returner on this row" -- confirmed by checking a real match where the columns stayed fixed to Player 1/2 while server/returner swapped. Summing base buckets + their `-1`/`-2` children double-counts, same nesting trap as svbreaktotal. |

## Joining rules
- Joining matches with points (or any stats_* table) repeats each match row once per
  point/breakdown-row. Never SUM or COUNT columns from matches after that join; use
  COUNT(DISTINCT match_id), or aggregate points/stats first in a subquery, then join.
- Answer point-level questions (serve, rally, pressure points) from points alone
  whenever possible; join matches only for extra match information (e.g. surface, date).
- For any stats_* table, check what its breakdown column's aggregate value is called
  (Total / STotal / RTotal / not present at all -- see the table above) before summing rows,
  and check whether categories are nested (e.g. stats_svbreaktotal's '4' already contains
  '4a'+'4d'; stats_rally's '1-3' already contains '1-3-1'+'1-3-2').
- stats_rally is keyed by (server, returner), which can swap per row within the same match --
  filter with `server = X OR returner = X` to get one player's rows regardless of who served,
  but read the result from the fixed `pl1_won`/`pl2_won` columns (tied to Player 1/2 from
  `matches`), not from `server`/`returner` positionally.

## Known data quality issues
- matches has a small number of duplicate match_id rows.
- stats_overview has a small number of duplicate (match_id, player, set) rows -- likely the
  same root cause as the matches duplicates.
- stats_returndepth has the same issue: 26 duplicate (match_id, player) combinations at
  `row = 'Total'`. Likely present in other stats_* tables too, not yet individually checked --
  if a total looks slightly inflated, check for duplicate (match_id, player[, row]) first.
- matches.Round has a handful of dirty values: venue names (e.g. "Emirates Arena") instead of
  a round code, one literal "1", 13 NaNs, and one "R64" with a trailing space that won't match
  a clean "R64" filter.
- **points."2nd" is NULL when no second serve was needed (the first serve went in) -- it is
  NOT an empty string `''`.** (Verified: 63,182 NULLs vs. 13 literal `''` rows on a sample.)
  A query that branches on `"2nd" = ''` to decide "was the first serve in" will silently match
  almost nothing for that branch, since `NULL = ''` is NULL (falsy) in SQL -- this can make a
  query that's supposed to check both "1st" and "2nd" only ever effectively check "2nd" AND
  only for points where the first serve actually faulted, badly undercounting anything that can
  happen on a first serve. Prefer checking `"1st" LIKE ...` and `"2nd" LIKE ...` independently
  with `OR`, rather than using a CASE/branch to pick one column based on `"2nd" = ''`. If you
  must branch, use `"2nd" IS NULL`, not `"2nd" = ''`.