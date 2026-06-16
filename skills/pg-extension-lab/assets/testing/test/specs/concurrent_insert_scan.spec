setup
{
  CREATE EXTENSION IF NOT EXISTS my_extension;
  CREATE TABLE IF NOT EXISTS t_items(id int PRIMARY KEY, v int);
  INSERT INTO t_items VALUES (1, 10), (2, 20) ON CONFLICT DO NOTHING;
}

teardown
{
  DROP TABLE IF EXISTS t_items;
}

session "s1"
step "s1_begin" { BEGIN; }
step "s1_insert" { INSERT INTO t_items VALUES (3, 30); }
step "s1_commit" { COMMIT; }

session "s2"
step "s2_begin" { BEGIN; }
step "s2_scan" { SELECT count(*) FROM t_items WHERE v >= 10; }
step "s2_commit" { COMMIT; }

permutation "s1_begin" "s1_insert" "s2_begin" "s2_scan" "s1_commit" "s2_commit"
permutation "s2_begin" "s2_scan" "s1_begin" "s1_insert" "s1_commit" "s2_commit"

