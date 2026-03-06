-- schema.sql

-- 1. Create a table for the matrix models
CREATE TABLE IF NOT EXISTS population_matrices (
    id SERIAL PRIMARY KEY,
    -- 'official' for COMADRE data, 'user' for custom ones
    source_type VARCHAR(20) DEFAULT 'official', 
    owner_id INTEGER DEFAULT NULL, -- Placeholder for future User table
    
    -- Core biological info for quick filtering
    species_accepted TEXT NOT NULL,
    common_name TEXT,
    kingdom TEXT,
    country_code CHAR(3),
    
    -- The Matrices (Stored as JSONB for efficiency)
    -- JSONB supports indexing and is faster for read/write than plain JSON
    matrix_s JSONB NOT NULL, -- e.g. [[0, 0], [0.9, 0]]
    matrix_f JSONB NOT NULL, -- e.g. [[0, 0.5], [0, 0]]
    
    -- Metadata blob for all the extra COMADRE fields (DOI, Authors, etc.)
    metadata JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Add an index for species search performance
CREATE INDEX idx_species ON population_matrices (species_accepted);