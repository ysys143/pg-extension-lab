\set ON_ERROR_STOP on

CREATE EXTENSION IF NOT EXISTS my_extension;

-- Replace with the smallest externally visible contract for the feature.
SELECT extname FROM pg_extension WHERE extname = 'my_extension';

