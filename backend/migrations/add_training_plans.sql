-- Migration: Add training plan tables
-- Branch: feat/training-plans-phase1

CREATE TABLE IF NOT EXISTS training_plans (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_distance_km FLOAT NOT NULL,
    race_name VARCHAR(200),
    race_date DATE NOT NULL,
    start_date DATE NOT NULL,
    days_per_week INTEGER NOT NULL,
    current_fitness_level VARCHAR(20) NOT NULL,
    template_key VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    total_weeks INTEGER NOT NULL,
    current_phase VARCHAR(10),
    vdot FLOAT,
    max_hr INTEGER,
    threshold_hr INTEGER,
    last_ai_review_at TIMESTAMP,
    ai_notes TEXT
);

CREATE INDEX IF NOT EXISTS ix_training_plans_user_id ON training_plans(user_id);
CREATE INDEX IF NOT EXISTS ix_training_plans_race_date ON training_plans(race_date);
CREATE INDEX IF NOT EXISTS ix_training_plans_status ON training_plans(status);
-- Only one active plan per user
CREATE UNIQUE INDEX IF NOT EXISTS ix_training_plans_user_active
    ON training_plans(user_id)
    WHERE status = 'active';

CREATE TABLE IF NOT EXISTS planned_workouts (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    plan_id INTEGER NOT NULL REFERENCES training_plans(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheduled_date DATE NOT NULL,
    day_of_week INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    phase VARCHAR(10) NOT NULL,
    workout_type VARCHAR(20) NOT NULL,
    target_distance_m FLOAT,
    target_duration_s INTEGER,
    target_pace_min_per_km FLOAT,
    target_pace_range JSONB,
    target_hr_zone INTEGER,
    structured_steps JSONB,
    description TEXT NOT NULL DEFAULT '',
    rationale TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'planned',
    matched_strava_id BIGINT REFERENCES strava_activities(strava_id),
    match_confidence FLOAT,
    perceived_effort INTEGER,
    user_notes TEXT
);

CREATE INDEX IF NOT EXISTS ix_planned_workouts_plan_id ON planned_workouts(plan_id);
CREATE INDEX IF NOT EXISTS ix_planned_workouts_user_id ON planned_workouts(user_id);
CREATE INDEX IF NOT EXISTS ix_planned_workouts_scheduled_date ON planned_workouts(scheduled_date);
CREATE INDEX IF NOT EXISTS ix_planned_workouts_user_date ON planned_workouts(user_id, scheduled_date);
CREATE INDEX IF NOT EXISTS ix_planned_workouts_status ON planned_workouts(status);
CREATE INDEX IF NOT EXISTS ix_planned_workouts_matched_strava ON planned_workouts(matched_strava_id);

CREATE TABLE IF NOT EXISTS training_paces (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    vdot FLOAT NOT NULL,
    easy_pace FLOAT NOT NULL,
    marathon_pace FLOAT NOT NULL,
    threshold_pace FLOAT NOT NULL,
    interval_pace FLOAT NOT NULL,
    repetition_pace FLOAT NOT NULL,
    max_hr INTEGER,
    threshold_hr INTEGER,
    resting_hr INTEGER,
    source_activity_ids JSONB,
    computed_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_training_paces_user_id ON training_paces(user_id);
