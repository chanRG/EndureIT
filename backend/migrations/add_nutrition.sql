-- Migration: Add nutrition and push subscription tables
-- Branch: feat/ai-nutrition-phase1

CREATE TABLE IF NOT EXISTS nutrition_plans (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_filename VARCHAR(255),
    source_pdf_url VARCHAR(500),
    raw_text TEXT,
    parsed_json JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'parsing',
    daily_calories_target FLOAT,
    daily_protein_g FLOAT,
    daily_carbs_g FLOAT,
    daily_fat_g FLOAT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS ix_nutrition_plans_user_id ON nutrition_plans(user_id);
-- One active plan per user
CREATE UNIQUE INDEX IF NOT EXISTS ix_nutrition_plans_user_active
    ON nutrition_plans(user_id)
    WHERE status = 'active';

CREATE TABLE IF NOT EXISTS nutrition_plan_meals (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    nutrition_plan_id INTEGER NOT NULL REFERENCES nutrition_plans(id) ON DELETE CASCADE,
    meal_slot VARCHAR(20) NOT NULL,
    default_time_local VARCHAR(5),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    calories FLOAT,
    protein_g FLOAT,
    carbs_g FLOAT,
    fat_g FLOAT,
    ingredients JSONB,
    ordering INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_nutrition_plan_meals_plan_id ON nutrition_plan_meals(nutrition_plan_id);

CREATE TABLE IF NOT EXISTS meal_variations (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    meal_id INTEGER NOT NULL REFERENCES nutrition_plan_meals(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    ingredients JSONB,
    calories FLOAT,
    protein_g FLOAT,
    carbs_g FLOAT,
    fat_g FLOAT,
    macro_drift JSONB,
    generated_by VARCHAR(10) NOT NULL DEFAULT 'ai',
    model_version VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS ix_meal_variations_meal_id ON meal_variations(meal_id);

CREATE TABLE IF NOT EXISTS nutrition_reminders (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_id INTEGER REFERENCES nutrition_plan_meals(id) ON DELETE SET NULL,
    planned_workout_id INTEGER REFERENCES planned_workouts(id) ON DELETE SET NULL,
    scheduled_at VARCHAR(30) NOT NULL,
    kind VARCHAR(30) NOT NULL,
    payload JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_nutrition_reminders_user_id ON nutrition_reminders(user_id);
CREATE INDEX IF NOT EXISTS ix_nutrition_reminders_user_scheduled
    ON nutrition_reminders(user_id, scheduled_at, status);

CREATE TABLE IF NOT EXISTS push_subscriptions (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL UNIQUE,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    user_agent VARCHAR(300),
    platform VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_success_at VARCHAR(30),
    error_count INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_push_subscriptions_user_id ON push_subscriptions(user_id);
