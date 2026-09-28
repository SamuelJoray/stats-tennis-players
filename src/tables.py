"""Registry mapping logical DuckDB table names to their source CSV globs.

Each entry's file pattern gets formatted twice, once per tour ('m' for men,
'w' for women), and the two results are combined with UNION ALL BY NAME into
one table with an extra `tour` column ('M' / 'W'). This keeps the schema the
agent sees small (one table per data category) instead of one per gender.
"""

DATA_DIR = "tennis_MatchChartingProject"

# -stats- categories, taken from the charting-{g}-stats-<Name>.csv filenames.
STATS_CATEGORIES = [
    "Overview",
    "ServeBasics",
    "ServeDirection",
    "ServeInfluence",
    "ReturnDepth",
    "ReturnOutcomes",
    "Rally",
    "ShotTypes",
    "ShotDirection",
    "ShotDirOutcomes",
    "SnV",
    "NetPoints",
    "SvBreakSplit",
    "SvBreakTotal",
    "KeyPointsServe",
    "KeyPointsReturn",
]

TABLES = {
    "matches": "charting-{g}-matches.csv",
    "points": "charting-{g}-points-*.csv",
}

for category in STATS_CATEGORIES:
    table_name = f"stats_{category.lower()}"
    TABLES[table_name] = f"charting-{{g}}-stats-{category}.csv"
