-- Run this in your Supabase SQL Editor to set up the fuel_log table
CREATE TABLE IF NOT EXISTS fuel_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    gas_price NUMERIC(5, 3),
    diesel_price NUMERIC(5, 3)
);