CREATE DATABASE esg_analysis;
USE esg_analysis;
DESCRIBE esg_kpi_summary;

-- Verifying the imported dataset

SHOW TABLES;

SELECT COUNT(*) FROM esg_energy_emissions_clean;
SELECT COUNT(*) FROM esg_workforce_social_clean;
SELECT COUNT(*) FROM esg_supplier_compliance_clean;
SELECT COUNT(*) FROM esg_governance_clean;
SELECT COUNT(*) FROM esg_kpi_summary;

-- Verifying

USE esg_analysis;

SELECT 'Energy'     AS dataset, COUNT(*) AS total_rows FROM esg_energy_emissions_clean
UNION ALL
SELECT 'Workforce'  AS dataset, COUNT(*) AS total_rows FROM esg_workforce_social_clean
UNION ALL
SELECT 'Supplier'   AS dataset, COUNT(*) AS total_rows FROM esg_supplier_compliance_clean
UNION ALL
SELECT 'Governance' AS dataset, COUNT(*) AS total_rows FROM esg_governance_clean
UNION ALL
SELECT 'KPI Summary' AS dataset, COUNT(*) AS total_rows FROM esg_kpi_summary;

-- Query 1 — Preview Each Table

SELECT * FROM esg_energy_emissions_clean LIMIT 5;
SELECT * FROM esg_workforce_social_clean LIMIT 5;
SELECT * FROM esg_supplier_compliance_clean LIMIT 5;
SELECT * FROM esg_governance_clean LIMIT 5;

-- Query 2 - Row Count Per Table

SELECT 'Energy'     AS dataset, COUNT(*) AS total_rows FROM esg_energy_emissions_clean
UNION ALL
SELECT 'Workforce'  AS dataset, COUNT(*) AS total_rows FROM esg_workforce_social_clean
UNION ALL
SELECT 'Supplier'   AS dataset, COUNT(*) AS total_rows FROM esg_supplier_compliance_clean
UNION ALL
SELECT 'Governance' AS dataset, COUNT(*) AS total_rows FROM esg_governance_clean;

-- Environmental Queries
-- Query 3 — Total Scope 1 and Scope 2 Emissions Per Year

SELECT
    year,
    scope,
    ROUND(SUM(emissions_tco2e), 2)        AS total_emissions,
    ROUND(AVG(emissions_tco2e), 4)        AS avg_emissions,
    COUNT(*)                               AS total_readings
FROM esg_energy_emissions_clean
WHERE scope IN ('Scope 1', 'Scope 2')
GROUP BY year, scope
ORDER BY year, scope;

-- Query 4 — Year Over Year Emissions Change Using LAG

WITH yearly_emissions AS (
    SELECT
        year,
        scope,
        ROUND(SUM(emissions_tco2e), 2) AS total_emissions
    FROM esg_energy_emissions_clean
    WHERE scope IN ('Scope 1', 'Scope 2')
    GROUP BY year, scope
)
SELECT
    year,
    scope,
    total_emissions,
    LAG(total_emissions) OVER (
        PARTITION BY scope ORDER BY year
    ) AS prev_year_emissions,
    ROUND(
        (total_emissions - LAG(total_emissions) OVER (
            PARTITION BY scope ORDER BY year
        )) / LAG(total_emissions) OVER (
            PARTITION BY scope ORDER BY year
        ) * 100, 2
    ) AS yoy_change_pct
FROM yearly_emissions
ORDER BY scope, year;

-- Query 5 — Emissions By Facility Ranked

SELECT
    facility_id,
    facility_name,
    country,
    region,
    year,
    ROUND(SUM(emissions_tco2e), 2) AS total_emissions,
    RANK() OVER (
        PARTITION BY year
        ORDER BY SUM(emissions_tco2e) DESC
    ) AS emissions_rank
FROM esg_energy_emissions_clean
WHERE scope IN ('Scope 1', 'Scope 2')
GROUP BY facility_id, facility_name, country, region, year
ORDER BY year, emissions_rank;

-- Query 6 — Top 3 Highest Emitting Facilities Per Year

WITH ranked_facilities AS (
    SELECT
        facility_id,
        facility_name,
        country,
        year,
        ROUND(SUM(emissions_tco2e), 2) AS total_emissions,
        RANK() OVER (
            PARTITION BY year
            ORDER BY SUM(emissions_tco2e) DESC
        ) AS emissions_rank
    FROM esg_energy_emissions_clean
    WHERE scope IN ('Scope 1', 'Scope 2')
    GROUP BY facility_id, facility_name, country, year
)
SELECT *
FROM ranked_facilities
WHERE emissions_rank <= 3
ORDER BY year, emissions_rank;

-- Query 7 — Emissions Per Production Unit By Facility

SELECT
    facility_id,
    facility_name,
    year,
    ROUND(SUM(emissions_tco2e), 2) AS total_emissions,
    MAX(facility_employees)         AS headcount,
    ROUND(
        SUM(emissions_tco2e) / MAX(facility_employees), 4
    )                               AS emissions_per_employee,
    RANK() OVER (
        PARTITION BY year
        ORDER BY SUM(emissions_tco2e) / MAX(facility_employees) DESC
    )                               AS intensity_rank
FROM esg_energy_emissions_clean
WHERE scope IN ('Scope 1', 'Scope 2')
GROUP BY facility_id, facility_name, year
ORDER BY year, intensity_rank;

-- Query 8 — Renewable Energy Adoption By Region Per Year

SELECT
    region,
    year,
    ROUND(SUM(CASE WHEN meter_type = 'Renewable Energy'
        THEN consumption ELSE 0 END), 2)                          AS renewable_consumption,
    ROUND(SUM(CASE WHEN meter_type IN ('Grid Electricity','Renewable Energy')
        THEN consumption ELSE 0 END), 2)                          AS total_electricity,
    ROUND(
        SUM(CASE WHEN meter_type = 'Renewable Energy'
            THEN consumption ELSE 0 END) /
        NULLIF(SUM(CASE WHEN meter_type IN ('Grid Electricity','Renewable Energy')
            THEN consumption ELSE 0 END), 0) * 100, 2
    ) AS renewable_pct
FROM esg_energy_emissions_clean
GROUP BY region, year
ORDER BY year, renewable_pct DESC;

-- Query 9 — Monthly Emissions Trend For Seasonal Analysis

SELECT
    year,
    month,
    month_name,
    quarter,
    ROUND(SUM(emissions_tco2e), 2) AS total_emissions,
    LAG(ROUND(SUM(emissions_tco2e), 2)) OVER (
        ORDER BY year, month
    ) AS prev_month_emissions
FROM esg_energy_emissions_clean
WHERE scope IN ('Scope 1', 'Scope 2')
GROUP BY year, month, month_name, quarter
ORDER BY year, month;

-- Social Queries
-- Query 10 — Gender Pay Gap By Facility And Year

SELECT
    facility_id,
    year,
    ROUND(AVG(CASE WHEN gender = 'Male'
        THEN current_salary END), 2)             AS avg_male_salary,
    ROUND(AVG(CASE WHEN gender = 'Female'
        THEN current_salary END), 2)             AS avg_female_salary,
    ROUND(
        (AVG(CASE WHEN gender = 'Male' THEN current_salary END) -
         AVG(CASE WHEN gender = 'Female' THEN current_salary END)) /
        AVG(CASE WHEN gender = 'Male' THEN current_salary END) * 100
    , 2)                                          AS gender_pay_gap_pct,
    CASE
        WHEN ROUND(
            (AVG(CASE WHEN gender = 'Male' THEN current_salary END) -
             AVG(CASE WHEN gender = 'Female' THEN current_salary END)) /
            AVG(CASE WHEN gender = 'Male' THEN current_salary END) * 100
        , 2) <= 5 THEN 'Meets Target'
        ELSE 'Below Target'
    END AS target_status
FROM esg_workforce_social_clean
GROUP BY facility_id, year
ORDER BY year, gender_pay_gap_pct DESC;

-- Query 11 — Leadership Diversity By Year

SELECT
    year,
    COUNT(*)                                              AS total_leadership,
    SUM(CASE WHEN gender = 'Female' THEN 1 ELSE 0 END)   AS female_leaders,
    SUM(CASE WHEN gender = 'Male' THEN 1 ELSE 0 END)     AS male_leaders,
    ROUND(
        SUM(CASE WHEN gender = 'Female' THEN 1 ELSE 0 END) /
        COUNT(*) * 100, 2
    )                                                     AS female_leadership_pct,
    CASE
        WHEN ROUND(
            SUM(CASE WHEN gender = 'Female' THEN 1 ELSE 0 END) /
            COUNT(*) * 100, 2
        ) >= 40 THEN 'Meets Target'
        ELSE 'Below Target'
    END AS target_status
FROM esg_workforce_social_clean
WHERE is_leadership = 'True'
GROUP BY year
ORDER BY year;

-- Query 12 — Injury Rate Per 100 Employees By Facility

SELECT
    facility_id,
    year,
    COUNT(*)                                               AS total_employees,
    SUM(CASE WHEN had_injury = 1 THEN 1 ELSE 0 END)       AS total_injuries,
    ROUND(
        SUM(CASE WHEN had_injury = 1 THEN 1 ELSE 0 END) /
        COUNT(*) * 100, 2
    )                                                      AS injury_rate_pct,
    CASE
        WHEN ROUND(
            SUM(CASE WHEN had_injury = 1 THEN 1 ELSE 0 END) /
            COUNT(*) * 100, 2
        ) <= 2.0 THEN 'Meets Target'
        ELSE 'Above Target'
    END AS target_status
FROM esg_workforce_social_clean
GROUP BY facility_id, year
ORDER BY year, injury_rate_pct DESC;

-- Query 13 — Training Hours Per Employee By Department

SELECT
    department,
    year,
    ROUND(AVG(training_hours), 2)  AS avg_training_hours,
    ROUND(MIN(training_hours), 2)  AS min_training_hours,
    ROUND(MAX(training_hours), 2)  AS max_training_hours,
    COUNT(*)                        AS employee_count,
    CASE
        WHEN ROUND(AVG(training_hours), 2) >= 40
        THEN 'Meets Target'
        ELSE 'Below Target'
    END AS target_status
FROM esg_workforce_social_clean
GROUP BY department, year
ORDER BY year, avg_training_hours DESC;

-- Query 14 — Workforce Turnover Rate By Year

SELECT
    year,
    COUNT(*)                                                  AS total_employees,
    SUM(CASE WHEN left_company = 1 THEN 1 ELSE 0 END)        AS employees_left,
    ROUND(
        SUM(CASE WHEN left_company = 1 THEN 1 ELSE 0 END) /
        COUNT(*) * 100, 2
    )                                                         AS turnover_rate_pct
FROM esg_workforce_social_clean
GROUP BY year
ORDER BY year;

-- Supplier Queries
-- Query 15 — Supplier Compliance Summary By Risk Profile

SELECT
    risk_profile,
    year,
    COUNT(*)                              AS total_audits,
    ROUND(AVG(audit_score), 2)            AS avg_audit_score,
    ROUND(AVG(labor_compliance_pct), 2)   AS avg_labor_compliance,
    ROUND(AVG(env_compliance_pct), 2)     AS avg_env_compliance,
    ROUND(AVG(safety_compliance_pct), 2)  AS avg_safety_compliance,
    SUM(non_conformances)                 AS total_non_conformances
FROM esg_supplier_compliance_clean
GROUP BY risk_profile, year
ORDER BY year, avg_audit_score ASC;

-- Query 16 — Failed And High Risk Suppliers

SELECT
    supplier_id,
    supplier_name,
    country,
    risk_profile,
    year,
    audit_score,
    labor_compliance_pct,
    non_conformances,
    audit_result
FROM esg_supplier_compliance_clean
WHERE audit_result IN ('Failed', 'Requires Improvement')
    AND risk_profile = 'High Risk'
ORDER BY year, audit_score ASC;

-- Query 17 — Supplier Improvement Trend Using LAG

WITH supplier_scores AS (
    SELECT
        supplier_id,
        supplier_name,
        year,
        ROUND(AVG(audit_score), 2) AS avg_score
    FROM esg_supplier_compliance_clean
    GROUP BY supplier_id, supplier_name, year
)
SELECT
    supplier_id,
    supplier_name,
    year,
    avg_score,
    LAG(avg_score) OVER (
        PARTITION BY supplier_id ORDER BY year
    ) AS prev_year_score,
    ROUND(
        avg_score - LAG(avg_score) OVER (
            PARTITION BY supplier_id ORDER BY year
        ), 2
    ) AS score_change,
    CASE
        WHEN avg_score > LAG(avg_score) OVER (
            PARTITION BY supplier_id ORDER BY year
        ) THEN 'Improving'
        WHEN avg_score < LAG(avg_score) OVER (
            PARTITION BY supplier_id ORDER BY year
        ) THEN 'Declining'
        ELSE 'Stable'
    END AS trend
FROM supplier_scores
ORDER BY supplier_id, year;

-- Query 18 — Labor Compliance By Country

SELECT
    country,
    year,
    COUNT(DISTINCT supplier_id)           AS total_suppliers,
    ROUND(AVG(labor_compliance_pct), 2)   AS avg_labor_compliance,
    CASE
        WHEN ROUND(AVG(labor_compliance_pct), 2) >= 90
        THEN 'Meets Target'
        ELSE 'Below Target'
    END AS target_status
FROM esg_supplier_compliance_clean
GROUP BY country, year
ORDER BY year, avg_labor_compliance ASC;

-- Governance Queries
-- Query 19 — Policy Compliance Rate By Facility Per Year

SELECT
    facility_id,
    facility_name,
    year,
    ROUND(AVG(policy_compliance_pct), 2)  AS avg_compliance_rate,
    ROUND(MIN(policy_compliance_pct), 2)  AS min_compliance,
    ROUND(MAX(policy_compliance_pct), 2)  AS max_compliance,
    CASE
        WHEN ROUND(AVG(policy_compliance_pct), 2) >= 95
        THEN 'Meets Target'
        ELSE 'Below Target'
    END AS target_status
FROM esg_governance_clean
GROUP BY facility_id, facility_name, year
ORDER BY year, avg_compliance_rate ASC;

-- Query 20 — Board Independence Progress

SELECT
    year,
    ROUND(AVG(board_independence_pct), 2)  AS avg_board_independence,
    ROUND(MIN(board_independence_pct), 2)  AS min_board_independence,
    ROUND(MAX(board_independence_pct), 2)  AS max_board_independence,
    SUM(CASE WHEN board_independence_pct >= 60
        THEN 1 ELSE 0 END)                 AS facilities_meeting_target,
    COUNT(DISTINCT facility_id)            AS total_facilities,
    CASE
        WHEN ROUND(AVG(board_independence_pct), 2) >= 60
        THEN 'Meets Target'
        ELSE 'Below Target'
    END AS overall_status
FROM esg_governance_clean
GROUP BY year
ORDER BY year;

-- Query 21 — Audit Finding Resolution Time Trend

WITH resolution_trend AS (
    SELECT
        year,
        facility_id,
        ROUND(AVG(avg_resolution_days), 1) AS avg_days
    FROM esg_governance_clean
    GROUP BY year, facility_id
)
SELECT
    year,
    facility_id,
    avg_days,
    LAG(avg_days) OVER (
        PARTITION BY facility_id ORDER BY year
    ) AS prev_year_days,
    ROUND(
        avg_days - LAG(avg_days) OVER (
            PARTITION BY facility_id ORDER BY year
        ), 1
    ) AS days_change,
    CASE
        WHEN avg_days <= 30 THEN 'Meets Target'
        WHEN avg_days <= 45 THEN 'Slightly Delayed'
        ELSE 'Significantly Delayed'
    END AS resolution_status
FROM resolution_trend
ORDER BY facility_id, year;

-- Query 22 — Data Breach Incidents By Year

SELECT
    year,
    SUM(data_breach_incidents)             AS total_breaches,
    COUNT(DISTINCT facility_id)            AS facilities_affected,
    ROUND(AVG(regulatory_fines_usd), 2)   AS avg_fine_usd,
    ROUND(SUM(regulatory_fines_usd), 2)   AS total_fines_usd
FROM esg_governance_clean
GROUP BY year
ORDER BY year;

-- Query 23 — Whistleblower Reports Trend

SELECT
    year,
    ROUND(AVG(whistleblower_per_1k), 2)   AS avg_reports_per_1k,
    ROUND(MIN(whistleblower_per_1k), 2)   AS min_reports,
    ROUND(MAX(whistleblower_per_1k), 2)   AS max_reports,
    CASE
        WHEN ROUND(AVG(whistleblower_per_1k), 2) <= 2.0
        THEN 'Meets Target'
        ELSE 'Above Target'
    END AS target_status
FROM esg_governance_clean
GROUP BY year
ORDER BY year;

-- ESG KPI Summary Queries
-- Query 24 — Complete ESG KPI vs Target Dashboard

SELECT
    year,
    scope1_tco2e,
    scope1_target,
    CASE WHEN scope1_tco2e <= scope1_target
        THEN 'On Track' ELSE 'Off Track' END        AS scope1_status,
    scope2_tco2e,
    scope2_target,
    CASE WHEN scope2_tco2e <= scope2_target
        THEN 'On Track' ELSE 'Off Track' END        AS scope2_status,
    gender_pay_gap_pct,
    gender_pay_gap_target,
    CASE WHEN gender_pay_gap_pct <= gender_pay_gap_target
        THEN 'On Track' ELSE 'Off Track' END        AS pay_gap_status,
    female_leadership_pct,
    female_leadership_target,
    CASE WHEN female_leadership_pct >= female_leadership_target
        THEN 'On Track' ELSE 'Off Track' END        AS leadership_status,
    board_independence_pct,
    board_target,
    CASE WHEN board_independence_pct >= board_target
        THEN 'On Track' ELSE 'Off Track' END        AS board_status,
    policy_compliance_pct,
    policy_target,
    CASE WHEN policy_compliance_pct >= policy_target
        THEN 'On Track' ELSE 'Off Track' END        AS policy_status,
    environmental_score,
    social_score,
    governance_score,
    overall_esg_score
FROM esg_kpi_summary
ORDER BY year;

-- Query 25 — ESG Score Trend Year Over Year

SELECT
    year,
    environmental_score,
    social_score,
    governance_score,
    overall_esg_score,
    LAG(overall_esg_score) OVER (ORDER BY year) AS prev_year_score,
    ROUND(
        overall_esg_score - LAG(overall_esg_score) OVER (ORDER BY year)
    , 2) AS score_change,
    CASE
        WHEN overall_esg_score > LAG(overall_esg_score) OVER (ORDER BY year)
        THEN 'Improving'
        WHEN overall_esg_score < LAG(overall_esg_score) OVER (ORDER BY year)
        THEN 'Declining'
        ELSE 'Stable'
    END AS overall_trend
FROM esg_kpi_summary
ORDER BY year;

 -- Query 26 — Count KPIs On Track vs Off Track Per Year

SELECT
    year,
    SUM(CASE WHEN scope1_tco2e <= scope1_target THEN 1 ELSE 0 END +
        CASE WHEN scope2_tco2e <= scope2_target THEN 1 ELSE 0 END +
        CASE WHEN gender_pay_gap_pct <= gender_pay_gap_target THEN 1 ELSE 0 END +
        CASE WHEN female_leadership_pct >= female_leadership_target THEN 1 ELSE 0 END +
        CASE WHEN board_independence_pct >= board_target THEN 1 ELSE 0 END +
        CASE WHEN policy_compliance_pct >= policy_target THEN 1 ELSE 0 END +
        CASE WHEN training_hours_avg >= training_target THEN 1 ELSE 0 END +
        CASE WHEN supplier_labor_compliance >= supplier_target THEN 1 ELSE 0 END +
        CASE WHEN data_breaches <= breach_target THEN 1 ELSE 0 END
    ) AS kpis_on_track,
    15 - SUM(
        CASE WHEN scope1_tco2e <= scope1_target THEN 1 ELSE 0 END +
        CASE WHEN scope2_tco2e <= scope2_target THEN 1 ELSE 0 END +
        CASE WHEN gender_pay_gap_pct <= gender_pay_gap_target THEN 1 ELSE 0 END +
        CASE WHEN female_leadership_pct >= female_leadership_target THEN 1 ELSE 0 END +
        CASE WHEN board_independence_pct >= board_target THEN 1 ELSE 0 END +
        CASE WHEN policy_compliance_pct >= policy_target THEN 1 ELSE 0 END +
        CASE WHEN training_hours_avg >= training_target THEN 1 ELSE 0 END +
        CASE WHEN supplier_labor_compliance >= supplier_target THEN 1 ELSE 0 END +
        CASE WHEN data_breaches <= breach_target THEN 1 ELSE 0 END
    ) AS kpis_off_track
FROM esg_kpi_summary
GROUP BY year
ORDER BY year;