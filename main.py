import duckdb

csv_path = "tennis_MatchChartingProject/charting-m-points-2020s.csv"

con = duckdb.connect()

# Load the CSV directly and peek at it
df = con.execute(f"SELECT * FROM read_csv_auto('{csv_path}') LIMIT 5").df()
print(df)

# Example query: how often does the server win the point, overall?
query = f"""
SELECT
    Svr,
    COUNT(*) AS total_points,
    SUM(CASE WHEN Svr = PtWinner THEN 1 ELSE 0 END) AS server_won,
    ROUND(100.0 * SUM(CASE WHEN Svr = PtWinner THEN 1 ELSE 0 END) / COUNT(*), 2) AS server_win_pct
FROM read_csv_auto('{csv_path}')
GROUP BY Svr
ORDER BY Svr
"""
result = con.execute(query).df()
print(result)
