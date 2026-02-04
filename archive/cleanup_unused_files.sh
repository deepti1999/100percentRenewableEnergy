#!/bin/bash

# Cleanup Script - Remove Unused Files and Archive Old Documentation
# Date: December 11, 2025

echo "=========================================="
echo "CLEANUP: Removing Unused Files"
echo "=========================================="
echo ""

# Navigate to project directory
cd "/Users/deeptimaheedharan/Desktop/total new try "

# 1. Delete unused Python scripts (5 files)
echo "1. Deleting unused Python scripts..."
rm -f check_all_formulas.py
rm -f generate_diagram.py
rm -f renewable_energy_complete_formulas.py
rm -f verbrauch_formulas_extracted.py
rm -f test_data_sources.py
echo "   ✓ Deleted 5 Python scripts"
echo ""

# 2. Delete old CSV files (13 files)
echo "2. Deleting old CSV files..."
rm -f biogas_full_hierarchy.csv
rm -f biogene_brennstoffe_fluessig_hierarchy.csv
rm -f biogene_brennstoffe_full_hierarchy.csv
rm -f endenergieangebot.csv
rm -f Gebaeudewaerme_exact_structure.csv
rm -f Gebaudewarme_fixed_values.csv
rm -f laufwasser_full_hierarchy.csv
rm -f renewable_energy_distribution_pypsa.csv
rm -f solar_energy.csv
rm -f stromwandlung_hierarchy.csv
rm -f tiefengeothermie_hierarchy.csv
rm -f umgebungswaerme_hierarchy.csv
rm -f windenergie_full_hierarchy.csv
echo "   ✓ Deleted 13 old CSV files"
echo ""

# 3. Delete logs and temp files (7 files)
echo "3. Deleting logs and temp files..."
rm -f FORMULA_FIXES.txt
rm -f PROMPTS.md
rm -f SECTION10_FORMULA_SUMMARY.txt
rm -f USE_CASE_DIAGRAM.md
rm -f system_architecture_diagram.png
rm -f runserver-8001.log
rm -f server.log
echo "   ✓ Deleted 7 logs/temp files"
echo ""

# 4. Archive outdated documentation (8 files)
echo "4. Archiving outdated documentation..."
mkdir -p archive/old_documentation
mv -f CHANGELOG.md archive/old_documentation/ 2>/dev/null
mv -f CONTEXT.md archive/old_documentation/ 2>/dev/null
mv -f EXTENSIBLE_FORMULA_SYSTEM.md archive/old_documentation/ 2>/dev/null
mv -f FILE_INVENTORY_COMPLETE.md archive/old_documentation/ 2>/dev/null
mv -f FORMULA_SYSTEM_STATUS.md archive/old_documentation/ 2>/dev/null
mv -f SYSTEM_COMPLETE.md archive/old_documentation/ 2>/dev/null
mv -f WEBAPP_BUTTONS_AND_WS366.md archive/old_documentation/ 2>/dev/null
mv -f WS_FORMULA_INTEGRATION.md archive/old_documentation/ 2>/dev/null
echo "   ✓ Moved 8 docs to archive/old_documentation/"
echo ""

# 5. Archive unused management commands (9 files)
echo "5. Archiving unused management commands..."
mkdir -p archive/unused_management_commands
mv -f simulator/management/commands/add_missing_gebaeudewaerme_rows.py archive/unused_management_commands/ 2>/dev/null
mv -f simulator/management/commands/clear_calculated_values.py archive/unused_management_commands/ 2>/dev/null
mv -f simulator/management/commands/extract_verbrauch_formulas.py archive/unused_management_commands/ 2>/dev/null
mv -f simulator/management/commands/import_clean.py archive/unused_management_commands/ 2>/dev/null
mv -f simulator/management/commands/load_endenergie_data.py archive/unused_management_commands/ 2>/dev/null
mv -f simulator/management/commands/load_exact_gebaeudewaerme.py archive/unused_management_commands/ 2>/dev/null
mv -f simulator/management/commands/migrate_gebaeudewaerme_to_verbrauch.py archive/unused_management_commands/ 2>/dev/null
mv -f simulator/management/commands/sync_renewable_formulas.py archive/unused_management_commands/ 2>/dev/null
mv -f simulator/management/commands/update_calculated_verbrauch.py archive/unused_management_commands/ 2>/dev/null
echo "   ✓ Moved 9 commands to archive/unused_management_commands/"
echo ""

# 6. Delete old backups (2 files)
echo "6. Deleting old model backups..."
rm -f archive/simulator/models.py.bak
rm -f archive/simulator/models.py.bak2
echo "   ✓ Deleted 2 backup files"
echo ""

# Summary
echo "=========================================="
echo "CLEANUP COMPLETE!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✓ Deleted 27 files (scripts, CSVs, logs, backups)"
echo "  ✓ Archived 17 files (docs, commands)"
echo ""
echo "Active codebase is now clean and focused!"
echo ""
echo "Remaining documentation:"
echo "  - README.md"
echo "  - PROJECT_DOCUMENTATION.md"
echo "  - FORMULA_DATABASE_STATUS.md (current)"
echo "  - WS_ROW_366_QUICK_REFERENCE.md"
echo "  - WS_ROW_366_UPDATE_DOCUMENTATION.md"
echo "  - UNUSED_FILES_ANALYSIS.md"
echo ""
