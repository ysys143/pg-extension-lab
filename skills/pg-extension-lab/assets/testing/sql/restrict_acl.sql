\set ON_ERROR_STOP on

-- Required edits:
--   :extension_schema  schema containing SECURITY DEFINER functions
--   :app_role          application role that may execute safe functions
--   :owner_role        extension owner role

REVOKE ALL ON SCHEMA :extension_schema FROM PUBLIC;
GRANT USAGE ON SCHEMA :extension_schema TO :app_role;

-- Audit SECURITY DEFINER functions missing search_path pinning.
SELECT n.nspname AS schema_name,
       p.proname AS function_name
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = :'extension_schema'
  AND p.prosecdef
  AND NOT EXISTS (
    SELECT 1
    FROM unnest(coalesce(p.proconfig, ARRAY[]::text[])) AS cfg
    WHERE cfg LIKE 'search_path=%'
  );

-- Audit publicly executable extension functions.
SELECT n.nspname AS schema_name,
       p.proname AS function_name
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = :'extension_schema'
  AND has_function_privilege('PUBLIC', p.oid, 'EXECUTE');

