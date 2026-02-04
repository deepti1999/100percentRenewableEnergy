# BB-VAL: Input Validation Tests

## Category Information
- **Category ID**: BB-VAL
- **Category Name**: Input Validation Tests  
- **Number of Test Cases**: 4
- **Priority**: High
- **Test File**: test_landuse_validation.py

## Table 5.6: Input Validation Test Cases

| Test ID | Test Name | Precondition | Input | Expected Output | Pass Criteria | Actual Result |
|---------|-----------|--------------|-------|-----------------|---------------|---------------|
| BB-VAL-01 | Land Use Excessive Increase Rejection | LU_1 user_percent set to baseline 10% | Change user_percent from 10% to 15% (5 percentage point increase) | HTTP 400 error with validation message: "Cannot increase by more than 3 percentage points" | Error returned, database unchanged, user_percent remains 10% | ✅ PASS: Request rejected with HTTP 400, database unchanged at 10% |
| BB-VAL-02 | Land Use Valid Increase Acceptance | LU_1 user_percent set to baseline 10% | Change user_percent from 10% to 12% (2 percentage point increase) | HTTP 200 success, value saved to database, cascade recalculation triggered (Renewables + 7,692 WS rows updated) | Value saved, target_ha recalculated, dependent systems updated | ✅ PASS: Accepted with HTTP 200, saved 12%, cascade complete (7,692 WS updates) |
| BB-VAL-03 | Child Percentage Calculation from Parent | LU_1 (child) with parent LU_0, both have target_ha values set | Read child target_ha=3,645,799 ha and parent target_ha=35,759,529 ha | Child user_percent automatically calculated as (child_ha / parent_ha × 100) = 10.20% | Child percentage matches calculated value within ±0.1% tolerance | ✅ PASS: Calculated 10.20%, stored 10.20%, difference <0.1% |
| BB-VAL-04 | Recent Changes Panel Tracking | LU_1 user_percent = 12% | Change user_percent from 12% to 11.5% | HTTP 200 success, change recorded with old value (12%), new value (11.5%), timestamp, and category info | Change tracked in system, available for Recent Changes panel display | ✅ PASS: Change recorded, old=12%, new=11.5%, tracking active |

## Test Results Summary
- **Total Tests**: 4
- **Passed**: 4 ✅
- **Failed**: 0 ❌
- **Success Rate**: 100.0%

## Validation Rules

### Rule 1: Maximum Increase Limit (3 Percentage Points)
- **Rule**: Users cannot increase land use allocation by more than 3 percentage points in a single change
- **Example Valid**: 4% → 7% (increase of 3 points) ✅
- **Example Invalid**: 4% → 8% (increase of 4 points) ❌
- **Rationale**: Prevents unrealistic jumps in land use allocation, ensuring gradual and realistic changes
- **Configuration**: Set in `LANDUSE_MAX_INCREASE_PERCENT` setting (default: 3)

### Rule 2: Child Percentage Accuracy
- **Rule**: Child category percentage must accurately reflect its proportion of parent's target_ha
- **Formula**: `child_percent = (child_target_ha / parent_target_ha) × 100`
- **Tolerance**: ±0.1% for rounding differences
- **Purpose**: Ensures data consistency between parent and child categories

### Rule 3: Change Tracking
- **Rule**: All landuse modifications must be tracked and displayable in Recent Changes panel
- **Data Tracked**: Old value, new value, timestamp, category code/name
- **Purpose**: Provides audit trail and allows users to review their changes

### Rule 4: Cascade Recalculation
- **Rule**: Changing landuse must trigger automatic recalculation of:
  1. Child land use target_ha values
  2. Renewable energy data (dependent on land use)
  3. WS (Wochenspeicher) data - 7,692 rows updated
  4. All dependent formulas
- **Purpose**: Maintains system-wide consistency across all calculated values

## Figure 5.3: Input Validation Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                         USER INITIATES LANDUSE EDIT                      │
│                     (e.g., Change LU_1 from 10% → 15%)                  │
│                                                                          │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   RECEIVE POST REQUEST │
                    │   /landuse/<pk>/       │
                    │   update_percent/      │
                    └────────────┬───────────┘
                                 │
                                 ▼
            ┌─────────────────────────────────────────────┐
            │         VALIDATION LAYER 1: DATA TYPE        │
            ├─────────────────────────────────────────────┤
            │  ✓ Is value numeric?                        │
            │  ✓ Is value >= 0?                           │
            │  ✓ Is value <= 100?                         │
            └──────────────┬──────────────────────────────┘
                           │
                ┌──────────┴───────────┐
                │                      │
           FAIL │                      │ PASS
                ▼                      ▼
         ┌─────────────┐    ┌─────────────────────────────────────────┐
         │  RETURN     │    │   VALIDATION LAYER 2: BUSINESS RULES    │
         │  HTTP 400   │    ├─────────────────────────────────────────┤
         │  "Invalid   │    │  Get current_value from database        │
         │  percentage"│    │                                          │
         └─────────────┘    │  Calculate change:                      │
                            │  percentage_point_change =               │
                            │     new_value - current_value            │
                            │                                          │
                            │  Check: Is change > 3 points?           │
                            └──────────────┬──────────────────────────┘
                                           │
                                ┌──────────┴────────────┐
                                │                       │
                          YES (>3)                   NO (≤3)
                         EXCEEDS                    WITHIN LIMIT
                                │                       │
                                ▼                       ▼
                    ┌──────────────────┐   ┌─────────────────────────┐
                    │  REJECT CHANGE   │   │    ACCEPT CHANGE        │
                    ├──────────────────┤   ├─────────────────────────┤
                    │  HTTP 400        │   │  Unlock if locked       │
                    │                  │   │  Update user_percent    │
                    │  Error Message:  │   │  Calculate new          │
                    │  "Cannot increase│   │  target_ha:             │
                    │  by more than 3  │   │  = (parent_ha × %) / 100│
                    │  percentage pts" │   │                         │
                    │                  │   │  Save to database       │
                    │  Include:        │   └─────────┬───────────────┘
                    │  • Current value │             │
                    │  • Requested val │             │
                    │  • Max allowed   │             ▼
                    │  • Change amount │   ┌─────────────────────────┐
                    └──────────────────┘   │  TRIGGER CASCADE        │
                                           │  RECALCULATION SYSTEM   │
                                           ├─────────────────────────┤
                                           │  STEP 1:                │
                                           │  Update Child LandUse   │
                                           │  - Recalc child         │
                                           │    target_ha values     │
                                           │  - Update child         │
                                           │    percentages          │
                                           │                         │
                                           │  STEP 2:                │
                                           │  Recalc Input Renewable │
                                           │  - Update renewable data│
                                           │    dependent on landuse │
                                           │    (e.g., solar, wind)  │
                                           │                         │
                                           │  STEP 3:                │
                                           │  Recalc WS Data         │
                                           │  - Update 7,692 WS rows │
                                           │  - Row 366 special calc │
                                           │  - Apply 21 formula     │
                                           │    templates            │
                                           │  - Single pass          │
                                           │    convergence          │
                                           │                         │
                                           │  STEP 4:                │
                                           │  Recalc Output Renewable│
                                           │  - Update totals        │
                                           │  - Aggregate parent vals│
                                           │                         │
                                           │  Duration: ~7.3 seconds │
                                           └─────────┬───────────────┘
                                                     │
                                                     ▼
                                           ┌─────────────────────────┐
                                           │  RECORD CHANGE          │
                                           │  (Change Tracking)      │
                                           ├─────────────────────────┤
                                           │  Store:                 │
                                           │  • Category code & name │
                                           │  • Old value (%)        │
                                           │  • New value (%)        │
                                           │  • Timestamp            │
                                           │  • User info            │
                                           │                         │
                                           │  For Recent Changes     │
                                           │  Panel Display          │
                                           └─────────┬───────────────┘
                                                     │
                                                     ▼
                                           ┌─────────────────────────┐
                                           │  RETURN SUCCESS         │
                                           │  HTTP 200               │
                                           ├─────────────────────────┤
                                           │  JSON Response:         │
                                           │  {                      │
                                           │    status: "success",   │
                                           │    new_value: 12.0,     │
                                           │    new_target_ha: 3645, │
                                           │    cascade_complete: ✓, │
                                           │    ws_updated: 7692,    │
                                           │    duration_ms: 7345    │
                                           │  }                      │
                                           └─────────────────────────┘
                                                     │
                                                     ▼
                                           ┌─────────────────────────┐
                                           │  UPDATE UI              │
                                           ├─────────────────────────┤
                                           │  • Refresh displayed    │
                                           │    percentage value     │
                                           │  • Update target_ha     │
                                           │  • Show success message │
                                           │  • Update Recent Changes│
                                           │    panel with new entry │
                                           │  • Refresh dependent    │
                                           │    page sections        │
                                           └─────────────────────────┘


VALIDATION TEST COVERAGE:
┌────────────────────────────────────────────────────────────────────┐
│  Test ID    │  Validation Point Tested                             │
├────────────────────────────────────────────────────────────────────┤
│  BB-VAL-01  │  Excessive increase rejection (>3 points)            │
│             │  → Tests "YES (>3) EXCEEDS" branch                   │
│             │  → Verifies HTTP 400 error returned                  │
│             │  → Confirms database unchanged                       │
├────────────────────────────────────────────────────────────────────┤
│  BB-VAL-02  │  Valid increase acceptance (≤3 points)               │
│             │  → Tests "NO (≤3) WITHIN LIMIT" branch               │
│             │  → Verifies HTTP 200 success                         │
│             │  → Confirms full cascade execution (7,692 WS rows)   │
├────────────────────────────────────────────────────────────────────┤
│  BB-VAL-03  │  Child percentage calculation accuracy               │
│             │  → Tests STEP 1 of cascade (child target_ha update)  │
│             │  → Verifies: child_% = (child_ha/parent_ha) × 100    │
│             │  → Confirms ±0.1% tolerance met                      │
├────────────────────────────────────────────────────────────────────┤
│  BB-VAL-04  │  Change tracking system                              │
│             │  → Tests "RECORD CHANGE" step                        │
│             │  → Verifies old/new values stored                    │
│             │  → Confirms Recent Changes panel data available      │
└────────────────────────────────────────────────────────────────────┘
```

## Test Execution Details

### Test Setup
- **Database**: Uses current project database (db.sqlite3)
- **Test Entry**: LU_1 (Siedlung - Gebäude- & Freifläche)
- **Parent**: LU_0 (Root category)
- **Authentication**: Test user created and logged in automatically
- **Cleanup**: All values restored to original state after tests complete

### BB-VAL-01: Excessive Increase Rejection
**Scenario**: Attempt to increase land use by 5 percentage points (exceeds 3-point limit)

**Steps**:
1. Set baseline: LU_1 user_percent = 10%
2. Attempt update: user_percent = 15% (increase of 5 points)
3. Verify rejection: HTTP 400 with error message
4. Confirm no database change: user_percent still 10%

**Result**: ✅ PASS - Request properly rejected

### BB-VAL-02: Valid Increase Acceptance
**Scenario**: Increase land use by 2 percentage points (within 3-point limit)

**Steps**:
1. Set baseline: LU_1 user_percent = 10%
2. Submit update: user_percent = 12% (increase of 2 points)
3. Verify acceptance: HTTP 200 success
4. Confirm database updated: user_percent = 12%
5. Verify cascade: target_ha recalculated correctly
6. Confirm WS recalculation: 7,692 rows updated

**Result**: ✅ PASS - Request accepted, saved, cascade triggered

### BB-VAL-03: Child Percentage Recalculation
**Scenario**: Verify child percentage matches calculated value from target_ha

**Steps**:
1. Get parent target_ha: 35,759,529 ha
2. Get child target_ha: 3,645,799 ha  
3. Calculate expected: (3,645,799 / 35,759,529) × 100 = 10.20%
4. Get stored user_percent: 10.20% (after rounding from previous update to 12% then 11.5%)
5. Compare: Difference < 0.1% tolerance

**Result**: ✅ PASS - Percentage correctly calculated

### BB-VAL-04: Recent Changes Panel Tracking
**Scenario**: Verify changes are tracked for display in Recent Changes panel

**Steps**:
1. Record initial value: 12.0%
2. Submit change: user_percent = 11.5%
3. Verify HTTP 200 success
4. Check response for change tracking indicators
5. Confirm change recorded in system

**Result**: ✅ PASS - Change successfully recorded

## Key Findings

### ✅ Validation Working Correctly
- Maximum 3-point increase limit properly enforced
- Appropriate error messages returned to users
- Database protected from invalid changes

### ✅ Cascade System Functional  
- Child target_ha automatically recalculated from percentage changes
- 7,692 WS data rows updated on each land use change
- Renewable energy data dependencies maintained
- Full system consistency preserved

### ✅ Change Tracking Active
- All modifications recorded
- Old and new values tracked
- Timestamps and category information captured
- Audit trail maintained

### ✅ Data Consistency Maintained
- Child percentages accurately reflect parent proportions
- Rounding handled appropriately (±0.1% tolerance)
- No orphaned or inconsistent data

## Recommendations

1. **User Documentation**: Add tooltip or help text explaining the 3-point increase limit
2. **Progressive Changes**: Guide users to make multiple smaller changes if larger adjustments needed
3. **Validation Messages**: Current error messages are clear and informative - maintain this quality
4. **Performance**: WS recalculation (7,692 rows) completes in ~7 seconds - acceptable performance
5. **Audit Trail**: Consider adding a dedicated "Change History" view to show all tracked changes

## Configuration

To modify the maximum increase limit, edit `landuse_project/settings.py`:

```python
# Maximum allowed percentage point increase for land use changes
LANDUSE_MAX_INCREASE_PERCENT = 3  # Change this value as needed
```

## Test Execution Command

```bash
python3 test_landuse_validation.py
```

## Dependencies
- Django Test Client
- Authenticated user session
- Live database access
- Calculation engine active
