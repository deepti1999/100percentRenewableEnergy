# Unused Files Analysis
## Complete Inventory of Redundant/Obsolete Files

**Date**: December 11, 2025  
**Status**: 221 formulas in database - All active code identified

---

## ✅ ACTIVE & REQUIRED FILES

### Core Application Files
```
manage.py                           ✅ Django entry point
db.sqlite3                          ✅ Database (221 formulas)
requirements.txt                    ✅ Dependencies
docker-compose.yml                  ✅ Docker setup
Dockerfile                          ✅ Docker setup
```

### Active Python Code
```
calculation_engine/
├── bilanz_engine.py               ✅ Bilanz calculations
├── formula_evaluator.py           ✅ Formula evaluation
├── landuse_engine.py              ✅ LandUse calculations
├── renewable_engine.py            ✅ Renewable calculations
└── verbrauch_engine.py            ✅ Verbrauch calculations

landuse_project/
├── settings.py                    ✅ Django settings
├── urls.py                        ✅ URL routing
├── wsgi.py                        ✅ WSGI server
└── asgi.py                        ✅ ASGI server

simulator/
├── models.py                      ✅ Database models
├── views.py                       ✅ Web views
├── admin.py                       ✅ Admin interface
├── urls.py                        ✅ URL routing
├── calculations.py                ✅ Renewable calculations (fallback)
├── verbrauch_calculations.py      ✅ Verbrauch calculations (fallback)
├── formula_service.py             ✅ Database-first formula loading
├── renewable_formulas.py          ✅ Formula registry
├── verbrauch_recalculator.py      ✅ Recalculation service
├── renewable_recalc.py            ✅ Renewable recalculation
├── recalc_service.py              ✅ Recalculation coordinator
├── goal_seek.py                   ✅ Goal seek solver
├── ws_models.py                   ✅ WS data models
└── gebaeudewaerme_recalculator.py ✅ Building heat recalculator
```

### Active Management Commands (11 commands)
```
simulator/management/commands/
├── import_formulas_to_db.py              ✅ Import renewable formulas (85)
├── import_verbrauch_formulas.py          ✅ Import verbrauch formulas (43)
├── add_missing_verbrauch_formulas.py     ✅ Import verbrauch formulas (49)
├── import_ws_formulas.py                 ✅ Import WS formulas (37)
├── import_landuse.py                     ✅ Import LandUse data
├── load_verbrauch_data.py                ✅ Load Verbrauch CSV data
├── load_gebaeudewaerme_data.py           ✅ Load building heat data
├── check_all_formulas.py                 ✅ Verify formula coverage
├── validate_formulas.py                  ✅ Validate formulas
├── recalc_verbrauch.py                   ✅ Recalculate Verbrauch
└── recalc_gebaeudewaerme.py              ✅ Recalculate building heat
```

### Active Data Files
```
CSV Files (Data Sources):
├── KLIK_Hierarchy_BlankForCalculated.csv           ✅ Main hierarchy
├── Flaechen_Daten_Clean.csv                        ✅ LandUse data
├── Flaechen_Daten_Hierarchie.csv                   ✅ LandUse hierarchy
├── Gebaeudewaerme_final_structure.csv              ✅ Building heat structure
├── renewable_sources_distribution_status.csv       ✅ Renewable distribution
├── renewable_sources_distribution_target.csv       ✅ Renewable targets
└── data/Actual_generation_*.csv                    ✅ Energy generation data
```

### Active Documentation
```
Documentation Files:
├── README.md                              ✅ Main documentation
├── PROJECT_DOCUMENTATION.md               ✅ Project overview
├── FORMULA_DATABASE_STATUS.md             ✅ Formula status (THIS IS CURRENT)
├── WS_ROW_366_QUICK_REFERENCE.md          ✅ WS row 366 reference
└── WS_ROW_366_UPDATE_DOCUMENTATION.md     ✅ WS update docs
```

---

## ❌ UNUSED / REDUNDANT FILES

### 1. Root Level - Unused Python Scripts (5 files)
**REASON**: One-time data extraction/testing, replaced by management commands

```
❌ check_all_formulas.py                   → Replaced by management command
❌ generate_diagram.py                      → One-time diagram generation
❌ renewable_energy_complete_formulas.py    → Data now in database
❌ verbrauch_formulas_extracted.py          → Data now in database
❌ test_data_sources.py                     → One-time test
```

**ACTION**: Safe to delete - functionality in database/management commands

---

### 2. Root Level - Outdated Documentation (8 files)
**REASON**: Superseded by FORMULA_DATABASE_STATUS.md

```
❌ CHANGELOG.md                             → Historical, not updated
❌ CONTEXT.md                               → Outdated context
❌ EXTENSIBLE_FORMULA_SYSTEM.md             → Old design docs
❌ FILE_INVENTORY_COMPLETE.md               → Old inventory
❌ FORMULA_SYSTEM_STATUS.md                 → Superseded by FORMULA_DATABASE_STATUS.md
❌ SYSTEM_COMPLETE.md                       → Old status
❌ WEBAPP_BUTTONS_AND_WS366.md              → Old WS docs
❌ WS_FORMULA_INTEGRATION.md                → Old integration docs
```

**KEEP**: 
```
✅ FORMULA_DATABASE_STATUS.md               → Current status (221 formulas)
✅ WS_ROW_366_QUICK_REFERENCE.md            → Still useful
✅ WS_ROW_366_UPDATE_DOCUMENTATION.md       → Still useful
```

**ACTION**: Archive old docs, keep current ones

---

### 3. Root Level - Temporary/Old CSV Files (14 files)
**REASON**: Intermediate processing files, data now in database

```
❌ biogas_full_hierarchy.csv
❌ biogene_brennstoffe_fluessig_hierarchy.csv
❌ biogene_brennstoffe_full_hierarchy.csv
❌ endenergieangebot.csv
❌ Gebaeudewaerme_exact_structure.csv       → Superseded by final_structure
❌ Gebaudewarme_fixed_values.csv
❌ laufwasser_full_hierarchy.csv
❌ renewable_energy_distribution_pypsa.csv
❌ solar_energy.csv                         → Superseded by solar_energy_updated.csv
❌ stromwandlung_hierarchy.csv
❌ tiefengeothermie_hierarchy.csv
❌ umgebungswaerme_hierarchy.csv
❌ windenergie_full_hierarchy.csv
```

**KEEP**:
```
✅ KLIK_Hierarchy_BlankForCalculated.csv
✅ Flaechen_Daten_Clean.csv
✅ Flaechen_Daten_Hierarchie.csv
✅ Gebaeudewaerme_final_structure.csv
✅ solar_energy_updated.csv
✅ renewable_sources_distribution_status.csv
✅ renewable_sources_distribution_target.csv
```

**ACTION**: Delete intermediate CSVs, keep final/active ones

---

### 4. Root Level - Other Unused Files (3 files)

```
❌ FORMULA_FIXES.txt                        → Historical notes
❌ PROMPTS.md                               → Development notes
❌ SECTION10_FORMULA_SUMMARY.txt            → Old summary
❌ USE_CASE_DIAGRAM.md                      → Old diagram
❌ system_architecture_diagram.png          → Old diagram
❌ runserver-8001.log                       → Log file
❌ server.log                               → Log file
```

**ACTION**: Delete logs and old notes

---

### 5. Archive Folder - OLD MIGRATION SCRIPTS (5 files)
**REASON**: One-time migration, data now in database

```
archive/old_migration_scripts/
├── ❌ fix_all_renewable_data.py           → Done, data in DB
├── ❌ fix_renewable_formulas.py           → Done, data in DB
├── ❌ import_renewable_data.py            → Replaced by management command
├── ❌ pypsa_renewable_sources_distribution.py → Done, data in DB
└── ❌ verify_renewable_against_excel.py   → One-time verification
```

**ACTION**: Keep in archive (already archived), but not needed for runtime

---

### 6. Archive Folder - OLD TEST SCRIPTS (87+ files!)
**REASON**: Development/testing/debugging scripts, no longer needed

```
archive/old_test_scripts/
├── ❌ add_prozesswaerme_data.py
├── ❌ calculate_*.py (multiple calculation tests)
├── ❌ check_*.py (multiple check scripts)
├── ❌ correct_*.py (one-time corrections)
├── ❌ debug_*.py (debugging scripts)
├── ❌ extract_verbrauch_formulas.py
├── ❌ final_comprehensive_test.py
├── ❌ find_*.py (search scripts)
├── ❌ fix_*.py (one-time fixes - MANY)
├── ❌ import_*.py (old import scripts - MANY)
├── ❌ pypsa_*.py (PyPSA experiments)
├── ❌ remove_specific_decimals.py
├── ❌ renewable_energy_complete_formulas.py → Duplicate
├── ❌ restore_decimal_values.py
├── ❌ shell_import.py
├── ❌ show_*.py (display scripts)
├── ❌ test_*.py (test scripts - MANY)
├── ❌ update_*.py (one-time updates - MANY)
└── ❌ verify_*.py (verification scripts)
```

**Total**: ~87 files, all one-time use

**ACTION**: Keep in archive folder (already archived), but could be deleted

---

### 7. Archive Folder - SCRIPTS (36 files)
**REASON**: WS calculation scripts - mostly one-time setup

```
archive/scripts/
├── ❌ add_4_more_rows.py
├── ❌ add_ws_sample_data.py
├── ❌ calculate_*.py (WS calculations - MANY)
├── ❌ final_import.py
├── ❌ import_ws_data.py
├── ❌ interactive_balancing_system.html
├── ❌ link_ws_to_*.py
├── ❌ migrate_landuse_codes.py
├── ❌ mobile_anwendungen_hierarchy.py
├── ❌ pypsa_analysis.html
├── ❌ pypsa_analysis.py
├── ❌ pypsa_timeseries.csv
├── ❌ rollback_landuse_codes.py
├── ❌ show_annual_electricity_summary.py
├── ❌ sum_stromverbr.py
├── ❌ update_*.py (WS updates)
├── ❌ use_case_diagram.html
└── ❌ verify_ws_366.py
```

**Total**: 36 files, mostly one-time use

**ACTION**: Keep in archive (already archived), but not needed for runtime

---

### 8. Archive Folder - SIMULATOR BACKUPS (2 files)

```
archive/simulator/
├── ❌ models.py.bak                       → Old backup
└── ❌ models.py.bak2                      → Old backup
```

**ACTION**: Can be deleted (backups of old code)

---

### 9. Unused Management Commands (7 files)
**REASON**: One-time use, development/testing, or obsolete

```
simulator/management/commands/
├── ❌ add_missing_gebaeudewaerme_rows.py  → One-time fix
├── ❌ clear_calculated_values.py          → Utility (rarely used)
├── ❌ extract_verbrauch_formulas.py       → One-time extraction
├── ❌ import_clean.py                     → Old import
├── ❌ load_endenergie_data.py             → One-time load
├── ❌ load_exact_gebaeudewaerme.py        → One-time load
├── ❌ migrate_gebaeudewaerme_to_verbrauch.py → One-time migration
├── ❌ sync_renewable_formulas.py          → Replaced by import_formulas_to_db
└── ❌ update_calculated_verbrauch.py      → One-time update
```

**KEEP (Active)**:
```
✅ import_formulas_to_db.py
✅ import_verbrauch_formulas.py
✅ add_missing_verbrauch_formulas.py
✅ import_ws_formulas.py
✅ import_landuse.py
✅ load_verbrauch_data.py
✅ load_gebaeudewaerme_data.py
✅ check_all_formulas.py
✅ validate_formulas.py
✅ recalc_verbrauch.py
✅ recalc_gebaeudewaerme.py
```

**ACTION**: Move unused commands to archive or delete

---

## 📊 SUMMARY

### Files to Keep (Core System)
| Category | Count | Status |
|----------|-------|--------|
| Core Django files | 7 | ✅ Required |
| Calculation engines | 5 | ✅ Required |
| Models/Views/Admin | 12 | ✅ Required |
| Active management commands | 11 | ✅ Required |
| Active CSV data files | 7 | ✅ Required |
| Current documentation | 3 | ✅ Required |
| **TOTAL ACTIVE** | **45** | **✅ Keep** |

### Files to Clean Up
| Category | Count | Status |
|----------|-------|--------|
| Root - Unused Python scripts | 5 | ❌ Delete |
| Root - Outdated docs | 8 | ❌ Archive |
| Root - Old CSV files | 14 | ❌ Delete |
| Root - Logs/temp files | 7 | ❌ Delete |
| archive/old_migration_scripts | 5 | ✅ Already archived |
| archive/old_test_scripts | 87 | ✅ Already archived |
| archive/scripts | 36 | ✅ Already archived |
| archive/simulator | 2 | ❌ Delete |
| Unused management commands | 9 | ❌ Move to archive |
| **TOTAL CLEANUP** | **173** | **❌ Clean** |

---

## 🎯 RECOMMENDED ACTIONS

### Immediate Actions (Safe to Delete)
1. **Delete root level unused files** (34 files):
   ```bash
   # Python scripts (5)
   rm check_all_formulas.py
   rm generate_diagram.py
   rm renewable_energy_complete_formulas.py
   rm verbrauch_formulas_extracted.py
   rm test_data_sources.py
   
   # Old CSV files (14)
   rm biogas_full_hierarchy.csv
   rm biogene_brennstoffe_fluessig_hierarchy.csv
   rm biogene_brennstoffe_full_hierarchy.csv
   rm endenergieangebot.csv
   rm Gebaeudewaerme_exact_structure.csv
   rm Gebaudewarme_fixed_values.csv
   rm laufwasser_full_hierarchy.csv
   rm renewable_energy_distribution_pypsa.csv
   rm solar_energy.csv
   rm stromwandlung_hierarchy.csv
   rm tiefengeothermie_hierarchy.csv
   rm umgebungswaerme_hierarchy.csv
   rm windenergie_full_hierarchy.csv
   
   # Logs and temp files (7)
   rm FORMULA_FIXES.txt
   rm PROMPTS.md
   rm SECTION10_FORMULA_SUMMARY.txt
   rm USE_CASE_DIAGRAM.md
   rm system_architecture_diagram.png
   rm runserver-8001.log
   rm server.log
   
   # Outdated docs (8) - Move to archive instead
   mv CHANGELOG.md archive/
   mv CONTEXT.md archive/
   mv EXTENSIBLE_FORMULA_SYSTEM.md archive/
   mv FILE_INVENTORY_COMPLETE.md archive/
   mv FORMULA_SYSTEM_STATUS.md archive/
   mv SYSTEM_COMPLETE.md archive/
   mv WEBAPP_BUTTONS_AND_WS366.md archive/
   mv WS_FORMULA_INTEGRATION.md archive/
   ```

2. **Move unused management commands to archive**:
   ```bash
   mkdir -p archive/unused_management_commands
   mv simulator/management/commands/add_missing_gebaeudewaerme_rows.py archive/unused_management_commands/
   mv simulator/management/commands/clear_calculated_values.py archive/unused_management_commands/
   mv simulator/management/commands/extract_verbrauch_formulas.py archive/unused_management_commands/
   mv simulator/management/commands/import_clean.py archive/unused_management_commands/
   mv simulator/management/commands/load_endenergie_data.py archive/unused_management_commands/
   mv simulator/management/commands/load_exact_gebaeudewaerme.py archive/unused_management_commands/
   mv simulator/management/commands/migrate_gebaeudewaerme_to_verbrauch.py archive/unused_management_commands/
   mv simulator/management/commands/sync_renewable_formulas.py archive/unused_management_commands/
   mv simulator/management/commands/update_calculated_verbrauch.py archive/unused_management_commands/
   ```

3. **Delete old backups**:
   ```bash
   rm archive/simulator/models.py.bak
   rm archive/simulator/models.py.bak2
   ```

### Optional Actions (Archive is Fine)
- Archive folder already contains 130+ old scripts
- These are already segregated and don't affect runtime
- **ACTION**: Keep as-is (already archived)

---

## ✅ RESULT AFTER CLEANUP

### Active Codebase Structure
```
project_root/
├── manage.py
├── db.sqlite3
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
│
├── calculation_engine/ (5 files)
├── landuse_project/ (4 files)
├── simulator/ (20+ core files)
│   └── management/commands/ (11 active commands)
│
├── data/ (energy generation CSVs)
├── CSV data files (7 active files)
│
├── Documentation/
│   ├── README.md
│   ├── PROJECT_DOCUMENTATION.md
│   ├── FORMULA_DATABASE_STATUS.md ⭐ CURRENT
│   ├── WS_ROW_366_QUICK_REFERENCE.md
│   └── WS_ROW_366_UPDATE_DOCUMENTATION.md
│
└── archive/ (old scripts - already segregated)
```

**Clean, focused, maintainable!**

---

## 🔍 VERIFICATION

All formulas are in database - no external Python files needed:
- ✅ 85 renewable formulas
- ✅ 92 verbrauch formulas  
- ✅ 37 WS formulas
- ✅ 7 landuse formulas
- **Total: 221 formulas in db.sqlite3**

All calculations use:
1. Database formulas (via FormulaService)
2. Fallback to hardcoded (calculations.py, verbrauch_calculations.py)

**System is self-contained and production-ready.**
