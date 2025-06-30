-- Initialize the database with some sample data
-- This file will be executed when the PostgreSQL container starts

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- The tables will be created automatically by SQLAlchemy
-- But we can add some initial data or additional configurations here

-- Create indexes for better performance
-- These will be created after the tables exist
DO $$
BEGIN
    -- Wait a moment for tables to be created by the application
    PERFORM pg_sleep(2);
    
    -- Create additional indexes if tables exist
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cars') THEN
        CREATE INDEX IF NOT EXISTS idx_cars_make_model ON cars(make, model);
        CREATE INDEX IF NOT EXISTS idx_cars_price ON cars(price);
        CREATE INDEX IF NOT EXISTS idx_cars_year ON cars(year);
        CREATE INDEX IF NOT EXISTS idx_cars_seller_id ON cars(seller_id);
        CREATE INDEX IF NOT EXISTS idx_cars_is_sold ON cars(is_sold);
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users') THEN
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    END IF;
END
$$;
