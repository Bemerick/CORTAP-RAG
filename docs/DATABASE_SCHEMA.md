# PostgreSQL Database Schema for FTA Compliance Guide

## Overview

This schema stores structured data from `FTA_Complete_Extraction.json` to enable fast, accurate queries for indicators, questions, and compliance information, including deficiencies and reviewer instructions.

---

## JSON Structure → Database Mapping

```
FTA_Complete_Extraction.json
├── metadata
└── sections[23]                    → compliance_sections table
    ├── section
    │   ├── id                      → section_code
    │   ├── title                   → section_name
    │   ├── page_range              → page_range
    │   └── purpose                 → purpose
    └── sub_areas[]                 → compliance_questions table
        ├── id                      → question_code (e.g., "TVI1")
        ├── question                → question_text
        ├── basic_requirement       → basic_requirement
        ├── applicability           → applicability
        ├── detailed_explanation    → detailed_explanation
        ├── instructions_for_reviewer → instructions_for_reviewer
        ├── indicators_of_compliance[] → compliance_indicators table
        │   ├── indicator_id        → letter (e.g., "a", "b", "c")
        │   └── text                → indicator_text
        └── deficiencies[]          → compliance_deficiencies table
            ├── code                → deficiency_code
            ├── title               → deficiency_title
            ├── determination       → determination
            └── suggested_corrective_action → corrective_action
```

---

## Tables

### 1. compliance_sections

Stores top-level compliance sections (Legal, Title VI, ADA, etc.)

```sql
CREATE TABLE compliance_sections (
    id SERIAL PRIMARY KEY,
    section_code VARCHAR(50) UNIQUE NOT NULL,     -- JSON: section.id (e.g., "TVI", "Legal", "F")
    section_name VARCHAR(255) NOT NULL,            -- JSON: section.title (e.g., "TITLE VI")
    page_range VARCHAR(50),                        -- JSON: section.page_range (e.g., "11-1 to 11-15")
    purpose TEXT,                                  -- JSON: section.purpose
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_section_code ON compliance_sections(section_code);
```

---

### 2. compliance_questions

Stores compliance questions (sub_areas in JSON) with all details

```sql
CREATE TABLE compliance_questions (
    id SERIAL PRIMARY KEY,
    section_id INTEGER NOT NULL REFERENCES compliance_sections(id) ON DELETE CASCADE,
    question_code VARCHAR(50) NOT NULL,            -- JSON: sub_areas[].id (e.g., "TVI1", "L2")
    question_text TEXT NOT NULL,                   -- JSON: sub_areas[].question
    basic_requirement TEXT,                        -- JSON: sub_areas[].basic_requirement
    applicability TEXT,                            -- JSON: sub_areas[].applicability
    detailed_explanation TEXT,                     -- JSON: sub_areas[].detailed_explanation
    instructions_for_reviewer TEXT,                -- JSON: sub_areas[].instructions_for_reviewer
    question_order INTEGER,                        -- Derived from array index
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(section_id, question_code)
);

-- Indexes
CREATE INDEX idx_question_code ON compliance_questions(question_code);
CREATE INDEX idx_section_questions ON compliance_questions(section_id);
CREATE INDEX idx_question_order ON compliance_questions(section_id, question_order);
CREATE INDEX idx_applicability ON compliance_questions(applicability);
```

---

### 3. compliance_indicators

Stores indicators of compliance (the lettered lists: a., b., c., etc.)

```sql
CREATE TABLE compliance_indicators (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES compliance_questions(id) ON DELETE CASCADE,
    letter VARCHAR(5) NOT NULL,                    -- JSON: indicators_of_compliance[].indicator_id (e.g., "a", "b", "c")
    indicator_text TEXT NOT NULL,                  -- JSON: indicators_of_compliance[].text
    indicator_order INTEGER,                       -- Derived from array index
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id, letter)
);

-- Indexes
CREATE INDEX idx_question_indicators ON compliance_indicators(question_id);
CREATE INDEX idx_indicator_order ON compliance_indicators(question_id, indicator_order);
```

---

### 4. compliance_deficiencies (NEW)

Stores potential deficiency determinations and corrective actions

```sql
CREATE TABLE compliance_deficiencies (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES compliance_questions(id) ON DELETE CASCADE,
    deficiency_code VARCHAR(50) NOT NULL,          -- JSON: deficiencies[].code (e.g., "L1-1", "TVI2-1")
    deficiency_title TEXT NOT NULL,                -- JSON: deficiencies[].title
    determination TEXT NOT NULL,                   -- JSON: deficiencies[].determination
    corrective_action TEXT,                        -- JSON: deficiencies[].suggested_corrective_action
    deficiency_order INTEGER,                      -- Derived from array index
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id, deficiency_code)
);

-- Indexes
CREATE INDEX idx_deficiency_code ON compliance_deficiencies(deficiency_code);
CREATE INDEX idx_question_deficiencies ON compliance_deficiencies(question_id);
```

---

## Complete Schema SQL

```sql
-- =====================================================
-- FTA Compliance Guide Database Schema
-- =====================================================

-- 1. Compliance Sections (23 top-level areas)
CREATE TABLE compliance_sections (
    id SERIAL PRIMARY KEY,
    section_code VARCHAR(50) UNIQUE NOT NULL,
    section_name VARCHAR(255) NOT NULL,
    page_range VARCHAR(50),
    purpose TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Compliance Questions (sub_areas)
CREATE TABLE compliance_questions (
    id SERIAL PRIMARY KEY,
    section_id INTEGER NOT NULL REFERENCES compliance_sections(id) ON DELETE CASCADE,
    question_code VARCHAR(50) NOT NULL,
    question_text TEXT NOT NULL,
    basic_requirement TEXT,
    applicability TEXT,
    detailed_explanation TEXT,
    instructions_for_reviewer TEXT,
    question_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(section_id, question_code)
);

-- 3. Compliance Indicators (lettered items: a, b, c...)
CREATE TABLE compliance_indicators (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES compliance_questions(id) ON DELETE CASCADE,
    letter VARCHAR(5) NOT NULL,
    indicator_text TEXT NOT NULL,
    indicator_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id, letter)
);

-- 4. Compliance Deficiencies (potential violations)
CREATE TABLE compliance_deficiencies (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES compliance_questions(id) ON DELETE CASCADE,
    deficiency_code VARCHAR(50) NOT NULL,
    deficiency_title TEXT NOT NULL,
    determination TEXT NOT NULL,
    corrective_action TEXT,
    deficiency_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id, deficiency_code)
);

-- =====================================================
-- Indexes for Fast Lookups
-- =====================================================

-- Sections
CREATE INDEX idx_section_code ON compliance_sections(section_code);

-- Questions
CREATE INDEX idx_question_code ON compliance_questions(question_code);
CREATE INDEX idx_section_questions ON compliance_questions(section_id);
CREATE INDEX idx_question_order ON compliance_questions(section_id, question_order);
CREATE INDEX idx_applicability ON compliance_questions(applicability);

-- Indicators
CREATE INDEX idx_question_indicators ON compliance_indicators(question_id);
CREATE INDEX idx_indicator_order ON compliance_indicators(question_id, indicator_order);

-- Deficiencies
CREATE INDEX idx_deficiency_code ON compliance_deficiencies(deficiency_code);
CREATE INDEX idx_question_deficiencies ON compliance_deficiencies(question_id);

-- =====================================================
-- Update Triggers
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_sections_updated_at
    BEFORE UPDATE ON compliance_sections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_questions_updated_at
    BEFORE UPDATE ON compliance_questions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_indicators_updated_at
    BEFORE UPDATE ON compliance_indicators
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_deficiencies_updated_at
    BEFORE UPDATE ON compliance_deficiencies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## Sample Queries

### 1. Get all indicators for Title VI (with question details)
```sql
SELECT
    cs.section_name,
    cq.question_code,
    cq.question_text,
    cq.applicability,
    ci.letter,
    ci.indicator_text
FROM compliance_sections cs
JOIN compliance_questions cq ON cs.id = cq.section_id
JOIN compliance_indicators ci ON cq.id = ci.question_id
WHERE cs.section_code = 'TVI'
ORDER BY cq.question_order, ci.indicator_order;
```

### 2. Get question with all related data (indicators + deficiencies)
```sql
SELECT
    cq.question_code,
    cq.question_text,
    cq.basic_requirement,
    cq.applicability,
    cq.instructions_for_reviewer,
    -- Aggregate indicators
    (
        SELECT json_agg(
            json_build_object(
                'letter', ci.letter,
                'text', ci.indicator_text
            ) ORDER BY ci.indicator_order
        )
        FROM compliance_indicators ci
        WHERE ci.question_id = cq.id
    ) as indicators,
    -- Aggregate deficiencies
    (
        SELECT json_agg(
            json_build_object(
                'code', cd.deficiency_code,
                'title', cd.deficiency_title,
                'determination', cd.determination,
                'corrective_action', cd.corrective_action
            ) ORDER BY cd.deficiency_order
        )
        FROM compliance_deficiencies cd
        WHERE cd.question_id = cq.id
    ) as deficiencies
FROM compliance_questions cq
WHERE cq.question_code = 'TVI1';
```

### 3. Find all deficiencies across all sections
```sql
SELECT
    cs.section_name,
    cq.question_code,
    cd.deficiency_code,
    cd.deficiency_title,
    cd.determination
FROM compliance_sections cs
JOIN compliance_questions cq ON cs.id = cq.section_id
JOIN compliance_deficiencies cd ON cq.id = cd.question_id
ORDER BY cs.section_code, cd.deficiency_code;
```

### 4. Search for specific corrective actions
```sql
SELECT
    cs.section_name,
    cq.question_code,
    cd.deficiency_code,
    cd.deficiency_title,
    cd.corrective_action
FROM compliance_deficiencies cd
JOIN compliance_questions cq ON cd.question_id = cq.id
JOIN compliance_sections cs ON cq.section_id = cs.id
WHERE cd.corrective_action ILIKE '%notify%FTA%'
ORDER BY cs.section_code;
```

### 5. Get reviewer instructions for a compliance area
```sql
SELECT
    cq.question_code,
    cq.question_text,
    cq.instructions_for_reviewer
FROM compliance_questions cq
JOIN compliance_sections cs ON cq.section_id = cs.id
WHERE cs.section_code = 'TVI'
    AND cq.instructions_for_reviewer IS NOT NULL
ORDER BY cq.question_order;
```

### 6. Analyze applicability distribution
```sql
SELECT
    applicability,
    COUNT(*) as question_count,
    array_agg(DISTINCT cs.section_name) as sections
FROM compliance_questions cq
JOIN compliance_sections cs ON cq.section_id = cs.id
WHERE applicability IS NOT NULL
GROUP BY applicability
ORDER BY question_count DESC;
```

### 7. Count deficiencies by section
```sql
SELECT
    cs.section_code,
    cs.section_name,
    COUNT(cd.id) as total_deficiencies
FROM compliance_sections cs
JOIN compliance_questions cq ON cs.id = cq.section_id
LEFT JOIN compliance_deficiencies cd ON cq.id = cd.question_id
GROUP BY cs.id, cs.section_code, cs.section_name
ORDER BY total_deficiencies DESC;
```

---

## Data Validation Queries

After ingestion, run these to validate:

```sql
-- 1. Total counts
SELECT
    'Sections' as table_name,
    COUNT(*) as row_count
FROM compliance_sections
UNION ALL
SELECT 'Questions', COUNT(*) FROM compliance_questions
UNION ALL
SELECT 'Indicators', COUNT(*) FROM compliance_indicators
UNION ALL
SELECT 'Deficiencies', COUNT(*) FROM compliance_deficiencies;

-- 2. Title VI validation (should have 11 questions, 25 indicators)
SELECT
    cs.section_name,
    COUNT(DISTINCT cq.id) as num_questions,
    COUNT(DISTINCT ci.id) as num_indicators,
    COUNT(DISTINCT cd.id) as num_deficiencies
FROM compliance_sections cs
JOIN compliance_questions cq ON cs.id = cq.section_id
LEFT JOIN compliance_indicators ci ON cq.id = ci.question_id
LEFT JOIN compliance_deficiencies cd ON cq.id = cd.question_id
WHERE cs.section_code = 'TVI'
GROUP BY cs.id, cs.section_name;

-- 3. Check for orphaned records (should all return 0)
SELECT
    'Orphaned Questions' as check_type,
    COUNT(*) as orphan_count
FROM compliance_questions
WHERE section_id NOT IN (SELECT id FROM compliance_sections)
UNION ALL
SELECT 'Orphaned Indicators', COUNT(*)
FROM compliance_indicators
WHERE question_id NOT IN (SELECT id FROM compliance_questions)
UNION ALL
SELECT 'Orphaned Deficiencies', COUNT(*)
FROM compliance_deficiencies
WHERE question_id NOT IN (SELECT id FROM compliance_questions);

-- 4. Find questions without indicators (might be valid, but good to check)
SELECT
    cs.section_code,
    cq.question_code,
    cq.question_text
FROM compliance_questions cq
JOIN compliance_sections cs ON cq.section_id = cs.id
WHERE cq.id NOT IN (SELECT DISTINCT question_id FROM compliance_indicators)
ORDER BY cs.section_code, cq.question_code;

-- 5. Find questions without deficiencies (also might be valid)
SELECT
    cs.section_code,
    cq.question_code,
    COUNT(ci.id) as indicator_count,
    COUNT(cd.id) as deficiency_count
FROM compliance_questions cq
JOIN compliance_sections cs ON cq.section_id = cs.id
LEFT JOIN compliance_indicators ci ON cq.id = ci.question_id
LEFT JOIN compliance_deficiencies cd ON cq.id = cd.question_id
GROUP BY cs.id, cs.section_code, cq.id, cq.question_code
HAVING COUNT(cd.id) = 0
ORDER BY cs.section_code, cq.question_code;
```

---

## JSON Field Mapping Reference

| Database Table | Database Field | JSON Path | Example Value |
|----------------|----------------|-----------|---------------|
| **compliance_sections** | | | |
| | section_code | `sections[].section.id` | "TVI" |
| | section_name | `sections[].section.title` | "TITLE VI" |
| | page_range | `sections[].section.page_range` | "11-1 to 11-15" |
| | purpose | `sections[].section.purpose` | "No person shall..." |
| **compliance_questions** | | | |
| | question_code | `sections[].sub_areas[].id` | "TVI1" |
| | question_text | `sections[].sub_areas[].question` | "Did the recipient..." |
| | basic_requirement | `sections[].sub_areas[].basic_requirement` | "A recipient is required..." |
| | applicability | `sections[].sub_areas[].applicability` | "All recipients" |
| | detailed_explanation | `sections[].sub_areas[].detailed_explanation` | "Every three years..." |
| | instructions_for_reviewer | `sections[].sub_areas[].instructions_for_reviewer` | "Review the Civil Rights..." |
| **compliance_indicators** | | | |
| | letter | `sections[].sub_areas[].indicators_of_compliance[].indicator_id` | "a" |
| | indicator_text | `sections[].sub_areas[].indicators_of_compliance[].text` | "Did the recipient develop..." |
| **compliance_deficiencies** | | | |
| | deficiency_code | `sections[].sub_areas[].deficiencies[].code` | "L1-1" |
| | deficiency_title | `sections[].sub_areas[].deficiencies[].title` | "Failure to notify FTA..." |
| | determination | `sections[].sub_areas[].deficiencies[].determination` | "The recipient is deficient if..." |
| | corrective_action | `sections[].sub_areas[].deficiencies[].suggested_corrective_action` | "The recipient must submit..." |

---

## Use Cases Enabled by Enhanced Schema

### 1. Full Question Analysis
Get everything about a specific question in one query:
- Question text and requirements
- Applicability scope
- All indicators to check
- All potential deficiencies
- Reviewer instructions

### 2. Deficiency Analysis
- Which sections have most deficiencies?
- What are common corrective actions?
- Search for specific violation types

### 3. Applicability Filtering
- Find all questions for "All recipients"
- Find transit-specific vs paratransit-specific requirements
- Segment questions by recipient type

### 4. Reviewer Workflow
- Get instructions for reviewing each area
- Know what to look for (indicators)
- Know what violations to check (deficiencies)

---

## Database Size Estimates (Updated)

Based on JSON structure:
- **23 sections** → compliance_sections: ~23 rows
- **~150-200 questions** → compliance_questions: ~175 rows
- **~400-500 indicators** → compliance_indicators: ~450 rows
- **~300-400 deficiencies** → compliance_deficiencies: ~350 rows

**Total database size**: ~2-3MB (still very lightweight)

---

## Performance Expectations

| Operation | Expected Latency |
|-----------|------------------|
| Get all indicators for one section | < 10ms |
| Get question with all details (indicators + deficiencies) | < 15ms |
| Count indicators/deficiencies across all sections | < 25ms |
| Search for specific deficiency code | < 5ms (indexed) |
| Full-text search in corrective actions | < 50ms |

---

## Example Data

### Sample Insertion for TVI1

```sql
-- Insert section
INSERT INTO compliance_sections (section_code, section_name, page_range, purpose)
VALUES (
    'TVI',
    'TITLE VI',
    '11-1 to 11-15',
    'No person shall, on the grounds of race, color, or national origin, be excluded from participation in, be denied the benefits of, or be subjected to discrimination under any program or activity receiving Federal financial assistance.'
) RETURNING id;  -- Let's say this returns id=10

-- Insert question
INSERT INTO compliance_questions (
    section_id,
    question_code,
    question_text,
    basic_requirement,
    applicability,
    detailed_explanation,
    instructions_for_reviewer,
    question_order
) VALUES (
    10,
    'TVI1',
    'Did the recipient prepare and submit a Title VI Program?',
    'A recipient is required to prepare and submit a Title VI Program based on the recipient''s transit-related characteristics.',
    'All recipients',
    'Every three years, all direct recipients must submit a Title VI program...',
    'Review the Civil Rights Status screen in TrAMS...',
    1
) RETURNING id;  -- Let's say this returns id=100

-- Insert indicators
INSERT INTO compliance_indicators (question_id, letter, indicator_text, indicator_order)
VALUES
    (100, 'a', 'Did the recipient develop and submit a Title VI Program in FTA''s TrAMS?', 1),
    (100, 'b', 'If the recipient submitted a Title VI Program and FTA has issued correspondence indicating required revisions, has the recipient made those revisions?', 2);

-- Insert deficiency
INSERT INTO compliance_deficiencies (
    question_id,
    deficiency_code,
    deficiency_title,
    determination,
    corrective_action,
    deficiency_order
) VALUES (
    100,
    'TVI1-1',
    'Title VI Program not submitted or expired',
    'The recipient is deficient if it did not submit a Title VI Program or program update.',
    'The recipient must develop and submit a complete Title VI Program in TrAMS at least 60 days prior to the expiration date of the program.',
    1
);
```

---

## Migration Strategy

1. **Create schema**: Run complete SQL schema above
2. **Validate structure**: Ensure all tables and indexes created
3. **Ingest data**: Use updated `ingest_json_to_db.py` (includes deficiencies)
4. **Verify counts**: Run validation queries
5. **Test queries**: Run sample queries for different use cases

---

**Status**: Enhanced Schema Design Complete
**Validated Against**: `FTA_Complete_Extraction.json`
**Tables**: 4 (sections, questions, indicators, deficiencies)
**Last Updated**: December 5, 2025
