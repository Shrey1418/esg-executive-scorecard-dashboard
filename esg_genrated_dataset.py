# ============================================================
# ESG ANALYTICS DATASET GENERATOR
# Target: 50,000+ rows across 4 data sources
# Company: Meridian Manufacturing Group
# Facilities: 12 | Employees: 8,000
# Period: January 2022 - December 2024 (3 years)
# ============================================================

import pandas as pd
import numpy as np
from faker import Faker
import random
import os
from datetime import datetime

np.random.seed(42)
random.seed(42)
fake = Faker()
Faker.seed(42)

os.makedirs('data', exist_ok=True)

# ============================================================
# MASTER REFERENCE DATA
# ============================================================

START_YEAR = 2022
END_YEAR   = 2024

facilities = {
    'FAC-001': {'name': 'Chicago Main Plant',    'country': 'USA',         'region': 'North America', 'size': 'Large',  'employees': 1200, 'prod_units': 85000},
    'FAC-002': {'name': 'Detroit Assembly',      'country': 'USA',         'region': 'North America', 'size': 'Large',  'employees': 950,  'prod_units': 72000},
    'FAC-003': {'name': 'Toronto Operations',    'country': 'Canada',      'region': 'North America', 'size': 'Medium', 'employees': 600,  'prod_units': 45000},
    'FAC-004': {'name': 'Munich Precision Works','country': 'Germany',     'region': 'Europe',        'size': 'Large',  'employees': 1100, 'prod_units': 80000},
    'FAC-005': {'name': 'Stuttgart Engineering', 'country': 'Germany',     'region': 'Europe',        'size': 'Medium', 'employees': 750,  'prod_units': 55000},
    'FAC-006': {'name': 'Rotterdam Hub',         'country': 'Netherlands', 'region': 'Europe',        'size': 'Medium', 'employees': 480,  'prod_units': 35000},
    'FAC-007': {'name': 'Lyon Components',       'country': 'France',      'region': 'Europe',        'size': 'Medium', 'employees': 520,  'prod_units': 38000},
    'FAC-008': {'name': 'Shanghai Manufacturing','country': 'China',       'region': 'Asia Pacific',  'size': 'Large',  'employees': 1400, 'prod_units': 110000},
    'FAC-009': {'name': 'Bangalore Tech Centre', 'country': 'India',       'region': 'Asia Pacific',  'size': 'Medium', 'employees': 680,  'prod_units': 48000},
    'FAC-010': {'name': 'Singapore Distribution','country': 'Singapore',   'region': 'Asia Pacific',  'size': 'Small',  'employees': 320,  'prod_units': 22000},
    'FAC-011': {'name': 'Monterrey Plant',       'country': 'Mexico',      'region': 'Latin America', 'size': 'Medium', 'employees': 580,  'prod_units': 42000},
    'FAC-012': {'name': 'Sao Paulo Operations',  'country': 'Brazil',      'region': 'Latin America', 'size': 'Small',  'employees': 420,  'prod_units': 30000},
}

departments  = ['Manufacturing','Engineering','Supply Chain','Finance','HR','Legal','IT','Sales']
job_levels   = ['Junior','Mid-Level','Senior','Manager','Director','VP','C-Suite']
level_weights= [0.25, 0.30, 0.20, 0.12, 0.07, 0.04, 0.02]

energy_meters = [
    'Natural Gas',      # Scope 1
    'Diesel',           # Scope 1
    'Grid Electricity', # Scope 2
    'Renewable Energy', # Scope 2
    'Water',            # non-GHG
    'Waste',            # non-GHG
]

# Improvement rate per facility (annual % reduction)
fac_improve = {fid: random.uniform(0.03, 0.10) for fid in facilities}

# ============================================================
# DATASET 1 — ENERGY & EMISSIONS (meter-level monthly)
# 12 facilities × 6 meters × 36 months = 2,592 base
# Multiply by ~10 shift records per meter  → ~25,920 rows
# ============================================================

print("Generating Dataset 1: Energy & Emissions...")

energy_records = []
rid = 1

meter_base = {          # (emission_factor_kgco2e_per_unit, unit_label, base_range)
    'Natural Gas':      (2.02,  'GJ',   (50,  400)),
    'Diesel':           (2.68,  'litres',(200, 2000)),
    'Grid Electricity': (0.45,  'MWh',  (100, 900)),
    'Renewable Energy': (0.01,  'MWh',  (20,  300)),
    'Water':            (0.0,   'm3',   (500, 4000)),
    'Waste':            (0.0,   'tonnes',(2,   40)),
}

for year in range(START_YEAR, END_YEAR + 1):
    ye = year - START_YEAR
    for month in range(1, 13):
        seasonal = 1.15 if month in [12,1,2] else (0.92 if month in [6,7,8] else 1.0)
        for fid, fi in facilities.items():
            improve = 1 - (fac_improve[fid] * ye)
            for meter in energy_meters:
                ef, unit, (lo, hi) = meter_base[meter]
                # Number of readings this meter this month (simulates shift/sub-meter logs)
                n_readings = random.randint(6, 12)
                for _ in range(n_readings):
                    base_consumption = np.random.uniform(lo, hi) * (fi['employees'] / 500)
                    consumption = round(base_consumption * improve * seasonal + np.random.normal(0, base_consumption * 0.05), 3)
                    consumption = max(0, consumption)
                    emissions_tco2e = round(consumption * ef / 1000, 4)

                    scope = 'Scope 1' if meter in ['Natural Gas','Diesel'] else \
                            'Scope 2' if meter in ['Grid Electricity','Renewable Energy'] else 'N/A'

                    energy_records.append({
                        'record_id':          f'ENV-{rid:07d}',
                        'year':               year,
                        'month':              month,
                        'month_name':         datetime(year,month,1).strftime('%B'),
                        'quarter':            f'Q{(month-1)//3+1}',
                        'fiscal_period':      f'{year}-{month:02d}',
                        'facility_id':        fid,
                        'facility_name':      fi['name'],
                        'country':            fi['country'],
                        'region':             fi['region'],
                        'facility_size':      fi['size'],
                        'facility_employees': fi['employees'],
                        'meter_type':         meter,
                        'scope':              scope,
                        'consumption':        consumption,
                        'unit':               unit,
                        'emissions_tco2e':    emissions_tco2e,
                        'improvement_factor': round(improve, 4),
                    })
                    rid += 1

df_energy = pd.DataFrame(energy_records)
print(f"  Energy rows: {len(df_energy):,}")

# ============================================================
# DATASET 2 — WORKFORCE (individual employee × year snapshot)
# 8,000 employees × 3 years = 24,000 rows
# ============================================================

print("Generating Dataset 2: Workforce & Social...")

# Build employee master once
emp_master = []
eid = 1
for fid, fi in facilities.items():
    for dept in departments:
        dept_headcount = max(1, fi['employees'] // len(departments))
        for _ in range(dept_headcount):
            gender    = random.choices(['Male','Female','Non-Binary'], weights=[0.58,0.38,0.04])[0]
            ethnicity = random.choices(['White','Asian','Hispanic','Black','Other'],
                                       weights=[0.52,0.22,0.13,0.09,0.04])[0]
            level     = random.choices(job_levels, weights=level_weights)[0]

            salary_map = {
                'Junior':    random.uniform(35000,  55000),
                'Mid-Level': random.uniform(55000,  80000),
                'Senior':    random.uniform(80000, 110000),
                'Manager':   random.uniform(100000,140000),
                'Director':  random.uniform(140000,200000),
                'VP':        random.uniform(200000,320000),
                'C-Suite':   random.uniform(320000,600000),
            }
            base_salary = salary_map[level]
            pay_adj = (random.uniform(0.82,0.95) if gender=='Female'
                       else random.uniform(0.88,0.97) if gender=='Non-Binary' else 1.0)

            emp_master.append({
                'employee_id': f'EMP-{eid:05d}',
                'facility_id': fid,
                'department':  dept,
                'gender':      gender,
                'ethnicity':   ethnicity,
                'job_level':   level,
                'is_leadership': level in ['Manager','Director','VP','C-Suite'],
                'base_salary': round(base_salary, 2),
                'actual_salary': round(base_salary * pay_adj, 2),
                'hire_year':   random.randint(2010, 2023),
            })
            eid += 1

emp_df = pd.DataFrame(emp_master)

workforce_records = []
wid = 1
for year in range(START_YEAR, END_YEAR + 1):
    ye = year - START_YEAR
    for _, emp in emp_df.iterrows():
        fi = facilities[emp['facility_id']]

        # Salary grows slightly each year
        salary_growth = 1 + (ye * random.uniform(0.02, 0.05))
        current_salary = round(emp['actual_salary'] * salary_growth, 2)

        # Training hours improve over time
        training_hours = round(min(80, 26 + ye * random.uniform(3,7) + np.random.normal(0,2)), 1)

        # Injury flag — low probability
        had_injury = random.random() < (0.04 - ye * 0.005)

        # Turnover flag — whether employee left this year
        left = random.random() < (0.15 - ye * 0.01)

        workforce_records.append({
            'record_id':              f'WF-{wid:07d}',
            'year':                   year,
            'employee_id':            emp['employee_id'],
            'facility_id':            emp['facility_id'],
            'facility_name':          fi['name'],
            'country':                fi['country'],
            'region':                 fi['region'],
            'department':             emp['department'],
            'gender':                 emp['gender'],
            'ethnicity':              emp['ethnicity'],
            'job_level':              emp['job_level'],
            'is_leadership':          emp['is_leadership'],
            'current_salary':         current_salary,
            'training_hours':         training_hours,
            'had_injury':             had_injury,
            'left_company':           left,
            'parental_leave_taken':   random.random() < 0.08,
        })
        wid += 1

df_workforce = pd.DataFrame(workforce_records)
print(f"  Workforce rows: {len(df_workforce):,}")

# ============================================================
# DATASET 3 — SUPPLIER COMPLIANCE (150 suppliers × audits)
# ~5,000 rows
# ============================================================

print("Generating Dataset 3: Supplier Compliance...")

sup_countries = {'China':0.28,'Germany':0.12,'USA':0.15,'India':0.10,
                 'Mexico':0.08,'Vietnam':0.07,'Brazil':0.05,'Taiwan':0.06,
                 'South Korea':0.05,'Other':0.04}
sup_cats = ['Raw Materials','Components','Packaging','Logistics',
            'IT Services','Facilities Management','Professional Services','Energy']

suppliers = [{
    'supplier_id':    f'SUP-{i:04d}',
    'supplier_name':  fake.company(),
    'category':       random.choice(sup_cats),
    'country':        random.choices(list(sup_countries.keys()), weights=list(sup_countries.values()))[0],
    'annual_spend':   round(random.uniform(50000, 5000000), 2),
    'risk_profile':   random.choices(['Low Risk','Medium Risk','High Risk'], weights=[0.45,0.35,0.20])[0],
    'is_critical':    random.random() < 0.30,
} for i in range(1, 151)]

sup_records = []
srid = 1
for year in range(START_YEAR, END_YEAR + 1):
    ye = year - START_YEAR
    for sup in suppliers:
        n_audits = random.randint(2,4) if sup['is_critical'] else random.randint(1,2)
        for audit_num in range(1, n_audits + 1):
            base = {'Low Risk':random.uniform(75,95),'Medium Risk':random.uniform(55,80),'High Risk':random.uniform(30,65)}[sup['risk_profile']]
            score = round(min(100, base + ye*random.uniform(1,4) + np.random.normal(0,3)), 2)
            nonconf = (random.randint(3,8) if score<60 else random.randint(1,4) if score<80 else random.randint(0,2))
            sup_records.append({
                'record_id':             f'SUP-{srid:06d}',
                'year':                  year,
                'audit_number':          audit_num,
                'supplier_id':           sup['supplier_id'],
                'supplier_name':         sup['supplier_name'],
                'category':              sup['category'],
                'country':               sup['country'],
                'annual_spend_usd':      sup['annual_spend'],
                'risk_profile':          sup['risk_profile'],
                'is_critical':           sup['is_critical'],
                'audit_score':           max(0, min(100, score)),
                'labor_compliance_pct':  max(0, min(100, round(score*random.uniform(0.90,1.05)+np.random.normal(0,2),2))),
                'env_compliance_pct':    max(0, min(100, round(score*random.uniform(0.85,1.05)+np.random.normal(0,3),2))),
                'safety_compliance_pct': max(0, min(100, round(score*random.uniform(0.88,1.05)+np.random.normal(0,2),2))),
                'non_conformances':      nonconf,
                'audit_result':          ('Approved' if score>=85 else 'Conditional Approval' if score>=65 else 'Requires Improvement' if score>=50 else 'Failed'),
                'corrective_action':     nonconf > 0,
            })
            srid += 1

df_supplier = pd.DataFrame(sup_records)
print(f"  Supplier rows: {len(df_supplier):,}")

# ============================================================
# DATASET 4 — GOVERNANCE (facility × month × policy area)
# 12 × 36 months × 10 policies = 4,320 rows
# ============================================================

print("Generating Dataset 4: Governance...")

policy_areas = ['Anti-Corruption','Data Privacy','Environmental','Health & Safety',
                'Human Rights','Whistleblower','Code of Conduct','Conflict of Interest',
                'Supplier Standards','Information Security']

gov_records = []
gid = 1
for year in range(START_YEAR, END_YEAR + 1):
    ye = year - START_YEAR
    for month in range(1, 13):
        for fid, fi in facilities.items():
            for policy in policy_areas:
                compliance_rate = round(min(99.5, 82 + ye*random.uniform(1.5,4) + np.random.normal(0,1.5)), 2)
                findings        = random.randint(0,5)
                resolved        = int(findings * random.uniform(0.6,1.0))
                resolution_days = round(max(5, 48 - ye*random.uniform(2,6) + np.random.normal(0,3)), 1)
                board_ind       = round(min(85, 46 + ye*random.uniform(2,5) + np.random.normal(0,1.5)), 2)
                whistleblower   = round(max(0, 3.5 - ye*random.uniform(0.1,0.4) + np.random.normal(0,0.2)), 2)
                data_breach     = 1 if random.random() < 0.015 else 0
                fine            = round(random.uniform(5000,150000),2) if random.random()<0.04 else 0
                training_pct    = round(min(100, 76 + ye*random.uniform(2,5) + np.random.normal(0,1.5)), 2)

                gov_records.append({
                    'record_id':                f'GOV-{gid:07d}',
                    'year':                     year,
                    'month':                    month,
                    'month_name':               datetime(year,month,1).strftime('%B'),
                    'quarter':                  f'Q{(month-1)//3+1}',
                    'fiscal_period':            f'{year}-{month:02d}',
                    'facility_id':              fid,
                    'facility_name':            fi['name'],
                    'country':                  fi['country'],
                    'region':                   fi['region'],
                    'policy_area':              policy,
                    'board_independence_pct':   board_ind,
                    'policy_compliance_pct':    max(0, compliance_rate),
                    'total_audit_findings':     findings,
                    'resolved_findings':        resolved,
                    'open_findings':            findings - resolved,
                    'avg_resolution_days':      resolution_days,
                    'whistleblower_per_1k':     whistleblower,
                    'data_breach_incidents':    data_breach,
                    'regulatory_fines_usd':     fine,
                    'compliance_training_pct':  training_pct,
                })
                gid += 1

df_governance = pd.DataFrame(gov_records)
print(f"  Governance rows: {len(df_governance):,}")

# ============================================================
# DATASET 5 — ESG KPI SUMMARY (3 rows — one per year)
# ============================================================

print("Generating Dataset 5: ESG KPI Summary...")
targets = {
    'scope1_reduction_target_pct': 20, 'scope2_reduction_target_pct': 30,
    'energy_intensity_reduction_pct': 15, 'water_reduction_pct': 10,
    'waste_diversion_target': 75, 'gender_pay_gap_target': 5,
    'female_leadership_target': 40, 'injury_rate_target': 2.0,
    'training_hours_target': 40, 'supplier_labor_target': 90,
    'board_independence_target': 60, 'policy_compliance_target': 95,
    'resolution_days_target': 30, 'whistleblower_target': 2.0,
    'data_breach_target': 0,
}

kpi_records = []
s1_base = df_energy[(df_energy['year']==2022)&(df_energy['scope']=='Scope 1')]['emissions_tco2e'].sum()
s2_base = df_energy[(df_energy['year']==2022)&(df_energy['scope']=='Scope 2')]['emissions_tco2e'].sum()

for year in range(START_YEAR, END_YEAR+1):
    ey  = df_energy[df_energy['year']==year]
    wy  = df_workforce[df_workforce['year']==year]
    sy  = df_supplier[df_supplier['year']==year]
    gy  = df_governance[df_governance['year']==year]

    s1  = ey[ey['scope']=='Scope 1']['emissions_tco2e'].sum()
    s2  = ey[ey['scope']=='Scope 2']['emissions_tco2e'].sum()

    male_sal   = wy[wy['gender']=='Male']['current_salary'].mean()
    female_sal = wy[wy['gender']=='Female']['current_salary'].mean()
    pay_gap    = round((male_sal - female_sal) / male_sal * 100, 2)

    leadership = wy[wy['is_leadership']==True]
    fem_lead   = round(len(leadership[leadership['gender']=='Female']) / max(1, len(leadership)) * 100, 2)
    injury_rt  = round(wy['had_injury'].sum() / len(wy) * 100, 2)

    env_score  = round(min(100, max(0,
        (1-(s1-s1_base*0.80)/s1_base)*100*0.30 +
        (1-(s2-s2_base*0.70)/s2_base)*100*0.35 +
        ey['consumption'][ey['meter_type']=='Waste'].count()*0.00 + 60*0.35)), 2)
    soc_score  = round(min(100, max(0,
        max(0,100-(pay_gap-5)*5)*0.25 +
        min(100,fem_lead*2.5)*0.25 +
        max(0,100-injury_rt*20)*0.25 +
        min(100,wy['training_hours'].mean()/40*100)*0.25)), 2)
    gov_score  = round(min(100, max(0,
        min(100,gy['board_independence_pct'].mean()/60*100)*0.30 +
        min(100,gy['policy_compliance_pct'].mean())*0.35 +
        max(0,100-(gy['avg_resolution_days'].mean()-30)*2)*0.35)), 2)
    overall    = round(env_score*0.40 + soc_score*0.35 + gov_score*0.25, 2)

    kpi_records.append({
        'year': year,
        'scope1_tco2e': round(s1,2), 'scope1_target': round(s1_base*(1-targets['scope1_reduction_target_pct']/100),2),
        'scope2_tco2e': round(s2,2), 'scope2_target': round(s2_base*(1-targets['scope2_reduction_target_pct']/100),2),
        'gender_pay_gap_pct': pay_gap, 'gender_pay_gap_target': targets['gender_pay_gap_target'],
        'female_leadership_pct': fem_lead, 'female_leadership_target': targets['female_leadership_target'],
        'injury_rate_pct': injury_rt, 'injury_rate_target': targets['injury_rate_target'],
        'training_hours_avg': round(wy['training_hours'].mean(),2), 'training_target': targets['training_hours_target'],
        'supplier_labor_compliance': round(sy['labor_compliance_pct'].mean(),2), 'supplier_target': targets['supplier_labor_target'],
        'board_independence_pct': round(gy['board_independence_pct'].mean(),2), 'board_target': targets['board_independence_target'],
        'policy_compliance_pct': round(gy['policy_compliance_pct'].mean(),2), 'policy_target': targets['policy_compliance_target'],
        'audit_resolution_days': round(gy['avg_resolution_days'].mean(),1), 'resolution_target': targets['resolution_days_target'],
        'whistleblower_per_1k': round(gy['whistleblower_per_1k'].mean(),2), 'whistleblower_target': targets['whistleblower_target'],
        'data_breaches': int(gy['data_breach_incidents'].sum()), 'breach_target': targets['data_breach_target'],
        'environmental_score': max(0,min(100,env_score)),
        'social_score':        max(0,min(100,soc_score)),
        'governance_score':    max(0,min(100,gov_score)),
        'overall_esg_score':   max(0,min(100,overall)),
    })

df_kpi = pd.DataFrame(kpi_records)
print(f"  KPI Summary rows: {len(df_kpi)}")

# ============================================================
# INTRODUCE DATA QUALITY ISSUES
# ============================================================
print("\nIntroducing data quality issues...")

# Energy nulls
ni = df_energy.sample(frac=0.015, random_state=42).index
df_energy.loc[ni, 'consumption'] = np.nan
# Energy duplicates
df_energy = pd.concat([df_energy, df_energy.sample(n=30, random_state=42)], ignore_index=True)
# Energy casing
ci = df_energy.sample(frac=0.02, random_state=42).index
df_energy.loc[ci, 'region'] = df_energy.loc[ci, 'region'].str.upper()

# Workforce nulls
wni = df_workforce.sample(frac=0.018, random_state=42).index
df_workforce.loc[wni, 'training_hours'] = np.nan
# Workforce duplicates
df_workforce = pd.concat([df_workforce, df_workforce.sample(n=50, random_state=42)], ignore_index=True)

# Supplier nulls
sni = df_supplier.sample(frac=0.025, random_state=42).index
df_supplier.loc[sni, 'audit_score'] = np.nan
# Supplier duplicates
df_supplier = pd.concat([df_supplier, df_supplier.sample(n=15, random_state=42)], ignore_index=True)

# Governance nulls
gni = df_governance.sample(frac=0.01, random_state=42).index
df_governance.loc[gni, 'regulatory_fines_usd'] = np.nan
# Governance duplicates
df_governance = pd.concat([df_governance, df_governance.sample(n=20, random_state=42)], ignore_index=True)

# ============================================================
# EXPORT
# ============================================================
print("\nExporting datasets...")
df_energy.to_csv('data/esg_energy_emissions_raw.csv',    index=False)
df_workforce.to_csv('data/esg_workforce_social_raw.csv', index=False)
df_supplier.to_csv('data/esg_supplier_compliance_raw.csv', index=False)
df_governance.to_csv('data/esg_governance_raw.csv',      index=False)
df_kpi.to_csv('data/esg_kpi_summary.csv',                index=False)

total = len(df_energy)+len(df_workforce)+len(df_supplier)+len(df_governance)
print("\n" + "="*55)
print("ESG DATASET GENERATION COMPLETE")
print("="*55)
print(f"Energy & Emissions:      {len(df_energy):>10,} rows")
print(f"Workforce & Social:      {len(df_workforce):>10,} rows")
print(f"Supplier Compliance:     {len(df_supplier):>10,} rows")
print(f"Governance:              {len(df_governance):>10,} rows")
print(f"KPI Summary:             {len(df_kpi):>10,} rows")
print(f"{'─'*40}")
print(f"TOTAL ROWS:              {total:>10,}")
print("="*55)