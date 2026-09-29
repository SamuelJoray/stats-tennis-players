# Table `points` (one row per point)


Example row:
match_id=20260521-M-Roland_Garros-Q3-Jesper_De_Jong-Michael_Zheng, Pt=92, Set1=0, Set2=1,
Gm1=1, Gm2=0, Pts=0-15, Gm#=14, TbSet=True, Svr=2, 1st=4b37y1r3n#, 2nd=, Notes=, PtWinner=2

## match_id
Format: `date-gender-tournament-round-player1-player2`, fields separated by `-`.
- date: yyyymmdd; gender: M (men) or W (women)
- tournament, player1, player2: spaces replaced by `_`
- round: Q1–Q3 = qualifying rounds; R128, R64, R32, R16 = round of 128/64/32/16
  (number of players remaining, so R128 comes before R64); QF, SF, F = quarter-final, semi-final, final.
"Player 1" and "player 2" everywhere below refer to the order of the names in match_id.

## Score columns (score BEFORE the point is played)
- Pt: point number within the match, starting at 1.
- Set1, Set2: sets won so far by player 1 / player 2.
- Gm1, Gm2: games won by player 1 / player 2 in the current set.
- Gm#: game number within the match, starting at 1.
- Pts: point score in the current game, SERVER'S SCORE FIRST (e.g. 30-40 = break point).   <!-- verify! -->
  Values: 0, 15, 30, 40, AD. In a tiebreak, Pts holds tiebreak points (e.g. 4-3).
- TbSet: True if the current set is decided by a tiebreak, False if it is an advantage set
  (played until one player leads by two games).

## Point columns
- Svr: which player serves this point: 1 = player 1, 2 = player 2.
- PtWinner: which player won the point: 1 or 2. "Server won the point" is Svr = PtWinner.
- 1st: coded rally starting with the first serve (see section "Shot codes").
  If the first serve is in, the whole rally is here and 2nd is empty.
- 2nd: if the first serve was a fault, the coded rally starting with the second serve.
  Empty if the first serve was in.
- Notes: free-text comments from the charter; usually empty.

---

# Table `matches` (one row per match)

Note on match_id: same format as documented above for `points`. Splitting match_id by `-` to
re-derive these fields is unreliable -- some tournament/venue names contain hyphens themselves
(e.g. "Boulogne-sur-Mer"), which shifts a naive split. Use this table's own columns instead;
only fall back to parsing match_id for tables (like `points`) that don't have them.

- `Player 1` / `Player 2`: full player names. Player 1 is whoever served first in the match --
  not a ranking or seeding.
- `Pl 1 hand` / `Pl 2 hand`: dominant hand, `'R'` or `'L'`. **Data quality**: of the 23 rows with
  a value outside `{'R','L'}`, 9 are genuinely corrupted (a date string, e.g. `'20221111'` --
  columns shifted for a handful of source rows), and the other 14 are just `'R '`/`'L '` with a
  trailing space, which won't match an exact `= 'R'` filter. Verify before trusting either an
  unusual value or an exact-match filter on this column.
- `Date`: match date, YYYYMMDD, as text.
- `Tournament`: tournament name, spaces replaced with `_`.
- `Round`: round code -- see `context/table_relationships.md` for the full list and known dirty
  rows (venue names leaking into this column, a stray `"R64 "` with trailing space, etc.).
- `Time`: match start time, free text, inconsistent formats (`"7:25 PM"`, `"7pm"`, `"14:00"` all
  appear) -- normalize before comparing/sorting by time.
- `Court`: court/venue name as free text (e.g. `"Stadium Court"`, `"Court 13"`), not a category.
- `Surface`: usually `Clay`/`Grass`/`Hard`. **Data quality**: same column-shift issue as `Pl 1
  hand` -- a small number of rows have a digit or even an umpire's name here instead.
- `Umpire`: chair umpire's name, often blank.
- `Best of`: number of sets needed to win the match (`'3'` or `'5'`). **Data quality**: 51 of
  11,830 rows are blank/NULL (just missing, not corrupted), and 2 rows have a genuinely corrupted
  value -- literally a player name, `'Zindaras'` -- same root cause as the `Pl 1 hand`/`Surface`
  issues. Always sanity-check `Best of` is actually `'1'`/`'3'`/`'5'` before filtering on it, and
  don't conflate "missing" with "corrupted" when reporting on data quality.
- `Final TB?`: intended to flag whether the final set is decided by a tiebreak/match-tiebreak
  rather than a full set. **Data quality: this column is heavily corrupted** -- observed values
  include stray single characters (`'A'`, `'N'`, `'V'`, `'W'`, `'T'`, `'S'`, `'0'`, `'1'`) that
  don't look like a clean flag. Treat any value here with real caution; don't assume it's a
  reliable boolean.
- `Charted by`: username/initials of the volunteer who charted the match.
- `tour`: `'M'` or `'W'` -- added by this project's own `scripts/build_db.py`, not present in
  the original per-gender CSVs.

---

# Columns shared across most `stats_*` tables

These names repeat across many of the 16 `stats_*` tables with the same meaning each time.
(The breakdown/category column itself -- usually called `row`, sometimes `set` -- is documented
per table in `context/table_relationships.md`, not here.)

**Serve/point outcome counts** (all counts, filtered to whatever category `row`/`set` selects):
- `pts` / `serve_pts` / `net_pts` / `snv_pts`: number of points in this row's category.
- `pts_won`: of those points, how many `player` won.
- `aces`, `dfs` (double faults), `unret` (unreturned serve -- returner never got the ball back
  in play, see "Unreturnables" in `context/points.md`), `forced_err`, `unforced`: standard point
  outcomes, same meaning as the shot-notation codes in `context/points.md`.
- `first_in` / `first_won`: first serves landed in / points won on those first serves.
- `second_in` / `second_won`: same, for second serve.
- `first_pts` / `first_pts_won` / `first_aces` / `first_unret` / `first_forced` /
  `first_won_lte_3_shots`: the same metrics again, but scoped to first-serve points only.
- `second_pts` / `second_pts_won` / `second_aces` / `second_unret` / `second_forced` /
  `second_won_lte_3_shots`: same, for second-serve points only.
- `pts_won_lte_3_shots`: points `player` won that ended within 3 shots total (a "cheap" point,
  via a strong serve or a quick winner).
- `bk_pts`: break points (faced while serving, or held while returning, depending on the table).
- `bp_saved`: break points saved while serving.
- `return_pts` / `return_pts_won`: points where `player` was returning / won while returning.

**Winners / errors, by shot side:**
- `winners`, `winners_fh`, `winners_bh`: outright winners (excludes aces), total / forehand /
  backhand.
- `unforced`, `unforced_fh`, `unforced_bh`: unforced errors, total / forehand / backhand.

**Serve direction:**
- `wide`, `body`, `t`: counts by serve direction, matching direction codes 4/5/6 in
  `context/points.md`.
- `deuce_wide`, `deuce_middle`, `deuce_t`, `ad_wide`, `ad_middle`, `ad_t`: serve counts by court
  side (deuce/ad) x direction. `"middle"` here means the same thing as `"body"` above (direction
  code 5 in `context/points.md`) -- just a different label used in this particular table.

**Rally shot direction:**
- `crosscourt`, `down_middle`, `down_the_line`, `inside_out`, `inside_in`: rally shot direction
  breakdown (distinct from serve direction above).

**Error type:**
- `err_net`, `err_wide`, `err_deep`, `err_wide_deep`, `err_foot`, `err_unknown`: error counts by
  type, matching the fault/error codes (n/w/d/x/g/e) in `context/points.md`.

**Shot-type tables (stats_shottypes, stats_shotdiroutcomes):**
- `shots`: number of shots of this row's type/category hit.
- `pt_ending`: how many of those shots ended the point (winner, error, or induced forced,
  combined) -- not independently verified against the other columns, sanity-check before relying
  on an exact breakdown.
- `induced_forced`: forced errors this shot type induced in the opponent.
- `serve_return`: how many of these shots were specifically a return of serve.
- `shots_in_pts_won` / `shots_in_pts_lost`: how many shots of this type occurred in points
  `player` eventually won / lost (not necessarily the point-ending shot).

**Return depth (stats_returndepth, stats_returnoutcomes):**
- `returnable`: serves the returner got a real racquet on.
- `returnable_won`: of those, how many `player` won (stats_returnoutcomes only).
- `shallow`, `deep`, `very_deep`: return depth breakdown, corresponding to the depth codes 7/8/9
  in `context/points.md`.
- `in_play` / `in_play_won`: returns that landed in play / points `player` won after such a
  return.

**Net play (stats_snv, stats_netpoints):**
- `net_winner` / `net_unforced`: winners / unforced errors hit specifically at the net.
- `passed_at_net`: times `player` was passed while at net.
- `passing_shot_induced_forced`: forced errors induced by an opponent's passing-shot attempt
  while `player` was at net.
- `return_forced` (stats_snv only): forced errors committed on the return of serve within a
  serve-and-volley point.
- `total_shots`: total shots hit within the filtered points.

**Key points (stats_keypointsserve, stats_keypointsreturn):**
- `svc_winners`: service winners -- serve wasn't an ace, but the returner couldn't mount a real
  reply (conceptually close to `unret`, but scoped to key points; don't assume identical).
- `rally_winners` / `rally_forced`: winners / forced errors that happened during the rally
  (as opposed to on the return/serve itself).

**stats_serveinfluence only:**
- `won_1+` through `won_10+`: **these are percentages stored as text** (e.g. `"68.8%"`), not raw
  counts -- the percentage of points `player` won when the rally reached at least N shots. Strip
  the `%` and cast to a number before doing arithmetic on them.

**stats_rally only:**
- `pl1_won`, `pl1_winners`, `pl1_forced`, `pl1_unforced`, `pl2_won`, `pl2_winners`, `pl2_forced`,
  `pl2_unforced`: the same "points won / winners / forced errors / unforced errors" metrics as
  above, but split by **Player 1 vs Player 2** (from `matches`) instead of by a `player` column.
  See `context/table_relationships.md` for the verified, occasionally counter-intuitive way
  these line up with the `server`/`returner` columns.