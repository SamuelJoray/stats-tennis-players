import duckdb

con = duckdb.connect("tennis.duckdb", read_only=True)

# Note: parsing the round out of match_id by splitting on '-' is unreliable --
# some tournament/venue names contain hyphens themselves (e.g. "Boulogne-sur-Mer"),
# which shifts the split and produces garbage. The `matches` table already has a
# proper, pre-parsed `Round` column, so use that instead.
query = """
SELECT "Round", COUNT(*) AS n_matches
FROM matches
GROUP BY "Round"
ORDER BY n_matches DESC
"""
result = con.execute(query).df()
print(result.to_string(index=False))
