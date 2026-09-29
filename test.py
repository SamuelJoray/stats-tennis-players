import duckdb

csv_path = "tennis_MatchChartingProject/charting-m-points-2020s.csv"

con = duckdb.connect()

# Load the CSV directly and peek at it
df = con.execute(f"SELECT * FROM read_csv_auto('{csv_path}')").df()


# Example query: how often does the server win the point, overall?
query_first_serve_in_on_T = f"""
SELECT COUNT(*) AS n_serves_T
FROM read_csv_auto('{csv_path}')
WHERE "1st" LIKE '6%'
  AND "1st" NOT LIKE '6n%'
  AND "1st" NOT LIKE '6w%'
  AND "1st" NOT LIKE '6d%'
  AND "1st" NOT LIKE '6x%'
  AND "1st" NOT LIKE '6g%'
  AND match_id LIKE '%Sinner%'
"""
result = con.execute(query_first_serve_in_on_T).df()
print(result)

# out on T
query_first_serve_out_on_T = f"""
SELECT COUNT(*) AS n_serves_T_out
FROM read_csv_auto('{csv_path}')
WHERE ("1st" LIKE '6n%'
  OR "1st" LIKE '6w%'
  OR "1st" LIKE '6d%'
  OR "1st" LIKE '6x%'
  OR "1st" LIKE '6g%')
  AND match_id LIKE '%Sinner%'
"""
result = con.execute(query_first_serve_out_on_T).df()
print(result)

# in on body
query_first_serve_in_on_body = f"""
SELECT COUNT(*) AS n_serves_body
FROM read_csv_auto('{csv_path}')
WHERE "1st" LIKE '5%'
  AND "1st" NOT LIKE '5n%'
  AND "1st" NOT LIKE '5w%'
  AND "1st" NOT LIKE '5d%'
  AND "1st" NOT LIKE '5x%'
  AND "1st" NOT LIKE '5g%'
  AND match_id LIKE '%Sinner%'
"""
result = con.execute(query_first_serve_in_on_body).df()
print(result)

# out on body
query_first_serve_out_on_body = f"""
SELECT COUNT(*) AS n_serves_body_out
FROM read_csv_auto('{csv_path}')
WHERE ("1st" LIKE '5n%'
  OR "1st" LIKE '5w%'
  OR "1st" LIKE '5d%'
  OR "1st" LIKE '5x%'
  OR "1st" LIKE '5g%')
  AND match_id LIKE '%Sinner%'
"""
result = con.execute(query_first_serve_out_on_body).df()
print(result)

# service exterieur in
query_first_serve_in_wide = f"""
SELECT COUNT(*) AS n_serves_wide
FROM read_csv_auto('{csv_path}')
WHERE "1st" LIKE '4%'
  AND "1st" NOT LIKE '4n%'
  AND "1st" NOT LIKE '4w%'
  AND "1st" NOT LIKE '4d%'
  AND "1st" NOT LIKE '4x%'
  AND "1st" NOT LIKE '4g%'
  AND match_id LIKE '%Sinner%'
"""
result = con.execute(query_first_serve_in_wide).df()
print(result)

# service exterieur out
query_first_serve_out_wide = f"""
SELECT COUNT(*) AS n_serves_wide_out
FROM read_csv_auto('{csv_path}')
WHERE ("1st" LIKE '4n%'
  OR "1st" LIKE '4w%'
  OR "1st" LIKE '4d%'
  OR "1st" LIKE '4x%'
  OR "1st" LIKE '4g%')
  AND match_id LIKE '%Sinner%'
"""
result = con.execute(query_first_serve_out_wide).df()
print(result)


# total serves in
query_first_serve_in = f"""
SELECT COUNT(*) AS n_serves_in
FROM read_csv_auto('{csv_path}')
WHERE ("1st" LIKE '4%' or "1st" LIKE '5%' or "1st" LIKE '6%')
    AND "1st" NOT LIKE '4n%'
    AND "1st" NOT LIKE '4w%'
    AND "1st" NOT LIKE '4d%'
    AND "1st" NOT LIKE '4x%'
    AND "1st" NOT LIKE '4g%'
    AND "1st" NOT LIKE '5n%'
    AND "1st" NOT LIKE '5w%'
    AND "1st" NOT LIKE '5d%'
    AND "1st" NOT LIKE '5x%'
    AND "1st" NOT LIKE '5g%'
    AND "1st" NOT LIKE '6n%'
    AND "1st" NOT LIKE '6w%'
    AND "1st" NOT LIKE '6d%'
    AND "1st" NOT LIKE '6x%'
    AND "1st" NOT LIKE '6g%'
    AND match_id LIKE '%Sinner%'
"""

result = con.execute(query_first_serve_in).df()
print(result)


query_first_serve_out = f"""
SELECT COUNT(*) AS n_serves_out
FROM read_csv_auto('{csv_path}')
WHERE ("1st" LIKE '4n%'
    OR "1st" LIKE '4w%'
    OR "1st" LIKE '4d%'
    OR "1st" LIKE '4x%'
    OR "1st" LIKE '4g%'
    OR "1st" LIKE '5n%'
    OR "1st" LIKE '5w%'
    OR "1st" LIKE '5d%'
    OR "1st" LIKE '5x%'
    OR "1st" LIKE '5g%'
    OR "1st" LIKE '6n%'
    OR "1st" LIKE '6w%'
    OR "1st" LIKE '6d%'
    OR "1st" LIKE '6x%'
    OR "1st" LIKE '6g%')
    AND match_id LIKE '%Sinner%'
"""

result = con.execute(query_first_serve_out).df()
print(result)


query_first_TbSet = f"""
SELECT TbSet, COUNT(*) FROM read_csv_auto('{csv_path}') GROUP BY TbSet;
"""

result = con.execute(query_first_TbSet).df()
print(result)
