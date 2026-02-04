# 3.8 Scenario Definition and Workflow

This section defines the operational scenarios within the 100ProSim system and describes the complete workflow from user input to system response, including data validation, calculation cascades, and balance operations.

---

## 3.8.1 System Scenarios Overview

The 100ProSim system supports multiple usage scenarios that enable users to model different renewable energy transition pathways. Each scenario involves specific user interactions, data modifications, and system responses.

### Primary Scenarios

**Scenario 1: Land Use Modification**
- **Purpose**: Adjust land allocation for renewable energy installations
- **User Role**: Energy planner, System administrator
- **Trigger**: User modifies percentage values in Land Use interface
- **System Response**: Validation, cascade calculation, renewable energy recalculation
- **Outcome**: Updated land use distribution and affected renewable energy values

**Scenario 2: Energy Consumption Adjustment**
- **Purpose**: Modify energy consumption parameters across sectors
- **User Role**: Energy analyst, Policy maker
- **Trigger**: User edits consumption values (percentages or absolute values)
- **System Response**: Validation, dependent field recalculation, balance update
- **Outcome**: Updated consumption patterns and balance sheet adjustments

**Scenario 3: Renewable Energy Balance Optimization**
- **Purpose**: Balance renewable energy supply with demand
- **User Role**: System operator, Energy engineer
- **Trigger**: User clicks balance button on Bilanz or Annual Electricity page
- **System Response**: Iterative balance algorithm execution (max 5 iterations)
- **Outcome**: Optimized energy storage values, balanced supply/demand

**Scenario 4: Complete System Recalculation**
- **Purpose**: Ensure all calculations are up-to-date across all modules
- **User Role**: System administrator
- **Trigger**: User clicks "Full Recalc" or "Unified Recalc" button
- **System Response**: Sequential execution of all calculation chains
- **Outcome**: Fully synchronized system state with all formulas evaluated

**Scenario 5: Baseline Management**
- **Purpose**: Create snapshots and restore previous system states
- **User Role**: System administrator, Testing personnel
- **Trigger**: User creates or restores baseline via API
- **System Response**: Database backup/restore operations
- **Outcome**: System state preserved or reverted to previous configuration

### Supporting Scenarios

**Scenario 6: Historical Data Analysis (SMARD Integration)**
- **Purpose**: Compare simulated values with historical generation data
- **User Role**: Data analyst, Researcher
- **Trigger**: User navigates to SMARD analysis page
- **System Response**: Visualization of 2023 generation data (Solar, Wind, Hydro)
- **Outcome**: Comparative insights between model and reality

**Scenario 7: Dashboard Monitoring**
- **Purpose**: View real-time system status and key metrics
- **User Role**: All authenticated users
- **Trigger**: User navigates to Cockpit dashboard
- **System Response**: Dynamic chart rendering with Status/Target toggle
- **Outcome**: Visual representation of renewable energy distribution

---

## 3.8.2 Complete End-to-End Workflow

This subsection describes the complete workflow from user input to final system response, integrating all components described in previous sections.

### Workflow Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    100ProSim Complete Workflow Architecture                  │
└─────────────────────────────────────────────────────────────────────────────┘

    User Interface Layer          Business Logic Layer         Data Layer
    ─────────────────────────    ──────────────────────    ─────────────────
          │                              │                        │
          │  1. User Action              │                        │
          │  (Edit/Click)                │                        │
          │                              │                        │
          ├──────────────────────────────▶                        │
          │  2. HTTP Request             │                        │
          │  (POST/GET)                  │  3. Authentication     │
          │                              │     & Authorization     │
          │                              │                        │
          │                              ├────────────────────────▶
          │                              │  4. Data Validation    │
          │                              │     & Rule Check       │
          │                              │                        │
          │                              │  5. Database Query     │
          │                              │     & Modification     │
          │                              │                        │
          │                              ├────────────────────────▶
          │                              │  6. Trigger Cascade    │
          │                              │     Calculations       │
          │                              │                        │
          │                              │  7. Formula            │
          │                              │     Evaluation         │
          │                              │                        │
          │                              ├────────────────────────▶
          │  8. HTTP Response            │  9. Balance Algorithm  │
          │     (JSON/HTML)              │     (if triggered)     │
          │                              │                        │
          ◀──────────────────────────────┤                        │
          │                              │ 10. Commit Changes     │
          │ 11. UI Update                │                        │
          │     (Display Results)        ├────────────────────────▶
          │                              │                        │
          ▼                              ▼                        ▼
```

### Detailed Workflow Steps

#### Phase 1: User Interaction

**Step 1.1: User Authentication**
- User accesses system via web browser
- Django session authentication validates user credentials
- Authenticated users receive access to protected simulation pages
- Unauthorized access redirects to login page

**Step 1.2: Page Navigation**
- User navigates to specific data interface (Land Use, Renewable, Verbrauch, Bilanz)
- Django view function queries database for current data state
- Template renders data in editable/read-only format based on field configuration
- JavaScript initializes client-side functionality (validation, auto-save, charts)

**Step 1.3: Data Input**
- User modifies editable field value
- Client-side JavaScript captures input event
- Real-time validation checks (format, range, data type)
- Visual feedback provided (field highlighting, error messages)

#### Phase 2: Request Processing

**Step 2.1: HTTP Request Transmission**
- JavaScript AJAX request sent to Django API endpoint
- Request includes: field identifier (code), new value, CSRF token
- Request method: POST for data modifications
- Content-Type: application/json or application/x-www-form-urlencoded

**Example API Endpoint Call:**
```javascript
// Land Use update example
fetch('/landuse/update_percent/' + pk + '/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
        new_percent: newValue
    })
});
```

**Step 2.2: Server-Side Authentication Check**
- Django middleware validates session token
- View decorator `@login_required` enforces authentication
- Permission checks for specific operations (if applicable)
- Invalid authentication returns HTTP 401/403

**Step 2.3: Input Validation**
- Backend validation layer processes input
- Validation rules applied based on data type:

**Land Use Validation Rules:**
- Maximum increase limit: 3 percentage points (configurable via settings)
- Negative values rejected
- Values exceeding 100% rejected
- Starting from 0%: any value up to 100% allowed
- Decreases: unlimited (no restriction)

**Energy Consumption Validation Rules:**
- User-editable field check (based on `user_editable` flag)
- Data type validation (numeric, percentage)
- Range validation (0-100% for percentages)
- Formula integrity check (read-only fields cannot be edited)

**Renewable Energy Validation Rules:**
- Fixed values protection (9.3.1, 9.3.4 not user-editable)
- Parent-child relationship integrity
- Calculation order preservation

#### Phase 3: Data Persistence

**Step 3.1: Database Transaction**
- Django ORM initiates database transaction
- UPDATE query modifies target record
- Timestamp fields updated (modified_at)
- Transaction committed on successful validation

**Example Database Update:**
```python
# Land Use update in views.py
landuse = get_object_or_404(LandUse, pk=pk)
landuse.user_percent = new_percent
landuse.save()  # Triggers Django signals
```

**Step 3.2: Signal Triggering**
- Django post_save signal activated
- Signal handlers in `signals.py` execute automatically
- Dependent calculations triggered based on modified field

**Signal Flow:**
```
LandUse.save() → post_save signal
    ↓
recalculate_renewable_status_from_landuse()
    ↓
Update Renewable 9.1.1, 9.1.2, 9.1.3, 9.1.4
    ↓
Cascade to child categories (9.1 → 9)
    ↓
Update WS (Hydrogen Storage) calculations (7692 formulas)
```

#### Phase 4: Calculation Cascade

**Step 4.1: Formula Resolution**
- FormulaVariable system resolves variable dependencies
- Formula expressions evaluated using Python eval() with restricted context
- Source types handled: landuse, renewable, verbrauch, ws_row_366, ws_current_row

**Formula Evaluation Example:**
```python
# Formula: "9.1.1 + 9.1.2 + 9.1.3 + 9.1.4"
# FormulaVariables map: 9.1.1 → RenewableData(code='9.1.1')
# Resolution: actual values fetched from database
# Evaluation: 150000 + 200000 + 100000 + 50000 = 500000
```

**Step 4.2: Hierarchical Calculation**
- Bottom-up calculation: leaf nodes → parent nodes
- Parent formula: sum of children
- Each level recalculated in sequence
- Circular dependency prevention (tree structure validation)

**Renewable Energy Hierarchy Example:**
```
9 (Total Renewable)
├── 9.1 (Solar)
│   ├── 9.1.1 (Ground PV) ← Land Use driven
│   ├── 9.1.2 (Roof PV) ← Land Use driven
│   ├── 9.1.3 (Facade PV) ← Land Use driven
│   └── 9.1.4 (Agri PV) ← Land Use driven
│   └── 9.1 = 9.1.1 + 9.1.2 + 9.1.3 + 9.1.4 (Formula)
├── 9.2 (Wind)
├── 9.3 (Storage)
│   ├── 9.3.1 (WS Electricity) ← Balance algorithm
│   └── 9.3.4 (WS Heat) ← Balance algorithm
└── 9 = 9.1 + 9.2 + 9.3 + ... (Formula)
```

**Step 4.3: Cross-Module Synchronization**
- WS (Hydrogen Storage) calculations synchronized
- 7,692 daily formulas evaluated (365 days × ~21 formulas/day)
- Row 366 (annual reference) updated
- Verbrauch (consumption) dependent fields recalculated

#### Phase 5: Balance Operations

**Step 5.1: Balance Algorithm Invocation**
- Triggered by user button click on Bilanz or Annual Electricity page
- API endpoint: `/api/balance-all/` or `/api/balance-energy/`
- Algorithm objective: minimize energy imbalance (supply vs. demand)

**Step 5.2: Iterative Balance Execution**
- Maximum iterations: 5
- Convergence tolerance: < 1% imbalance
- Each iteration adjusts WS storage values (9.3.1, 9.3.4)

**Balance Algorithm Pseudocode:**
```
function balance_all():
    for iteration in range(1, 6):
        // Step 1: Calculate energy balance
        total_supply = sum(renewable_supply)
        total_demand = sum(consumption_demand)
        imbalance = total_supply - total_demand
        
        // Step 2: Adjust WS storage
        ws_electricity_adjustment = imbalance * 0.7
        ws_heat_adjustment = imbalance * 0.3
        
        // Step 3: Update WS values
        RenewableData(code='9.3.1').status += ws_electricity_adjustment
        RenewableData(code='9.3.4').status += ws_heat_adjustment
        
        // Step 4: Recalculate WS formulas (7692 formulas)
        recalculate_ws_data()
        
        // Step 5: Check convergence
        if abs(imbalance) < convergence_threshold:
            return "Balance achieved in {iteration} iterations"
    
    return "Balance partially achieved after 5 iterations"
```

**Step 5.3: Balance Result Verification**
- Final balance sheet comparison
- Aktiva (supply) vs. Passiva (demand)
- Imbalance percentage calculation
- Result stored in database

#### Phase 6: Response Generation

**Step 6.1: Response Data Preparation**
- Updated values serialized to JSON
- Dependent field values included
- Calculation metadata (iteration count, convergence status)
- Error messages (if validation failed)

**Example JSON Response:**
```json
{
    "status": "success",
    "updated_code": "LU_2.1",
    "new_value": 35.5,
    "previous_value": 32.5,
    "affected_fields": [
        {"code": "9.1.1", "new_value": 175000},
        {"code": "9.1", "new_value": 550000},
        {"code": "9", "new_value": 1250000}
    ],
    "ws_calculations_triggered": true,
    "balance_iterations": 3,
    "message": "Land use updated and all calculations completed successfully"
}
```

**Step 6.2: HTTP Response Transmission**
- Response code: 200 (success), 400 (validation error), 500 (server error)
- Response headers: Content-Type: application/json
- Response body: JSON data or HTML (for full page loads)

#### Phase 7: UI Update

**Step 7.1: JavaScript Response Handling**
- AJAX success callback processes response
- DOM updated with new values
- Visual feedback: success messages, field highlighting
- Charts refreshed (if applicable)

**Step 7.2: UI State Synchronization**
- Editable fields updated with confirmed values
- Read-only calculated fields updated
- Status indicators refreshed (balance status, convergence)
- localStorage updated for session persistence

**Step 7.3: User Feedback**
- Toast notifications: success/error messages
- Field highlighting: green (success), orange (warning), red (error)
- Loading indicators hidden
- Enable user to continue editing

---

## 3.8.3 Data Flow Diagrams

### Diagram 1: Land Use to Renewable Energy Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Land Use → Renewable Energy Flow                   │
└──────────────────────────────────────────────────────────────────────┘

USER INPUT
    │
    │  Modify LU_2.1 (PV Ground)
    │  32.5% → 35.0%
    ▼
┌─────────────────────┐
│   Validation Layer  │
│  • 3-point limit OK │
│  • +2.5 < 3 ✓       │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  Database Update    │
│  LU_2.1.user_percent│
│  = 35.0%            │
└─────────────────────┘
    │
    │  Django Signal: post_save
    ▼
┌─────────────────────────────────────────────┐
│  recalculate_renewable_status_from_landuse()│
│  • Calculate new area (ha)                  │
│  • Apply solar_installation_percentage      │
│  • Calculate MWh/a from formula             │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────┐         ┌─────────────────────┐
│  9.1.1 (Ground PV)  │         │  9.1.2 (Roof PV)    │
│  Status: 150000 →   │         │  Status: 200000     │
│  175000 MWh/a       │         │  (unchanged)        │
└─────────────────────┘         └─────────────────────┘
    │                               │
    └───────────┬───────────────────┘
                ▼
    ┌───────────────────────┐
    │  9.1 (Solar Total)    │
    │  Formula: 9.1.1 +     │
    │  9.1.2 + 9.1.3 + 9.1.4│
    │  = 550000 MWh/a       │
    └───────────────────────┘
                │
                ▼
    ┌───────────────────────┐
    │  9 (Renewable Total)  │
    │  Formula: 9.1 + 9.2 + │
    │  9.3 + ... + 9.7      │
    │  = 1250000 MWh/a      │
    └───────────────────────┘
                │
                ▼
    ┌───────────────────────┐
    │  WS Calculations      │
    │  7692 formulas        │
    │  (365 days × 21)      │
    │  Updated via          │
    │  FormulaVariable      │
    └───────────────────────┘
                │
                ▼
    ┌───────────────────────┐
    │  UI Refresh           │
    │  All values updated   │
    │  User sees result     │
    └───────────────────────┘
```

### Diagram 2: Balance Algorithm Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                      Balance Algorithm Workflow                       │
└──────────────────────────────────────────────────────────────────────┘

USER ACTION
    │
    │  Click "Balance All" button
    │  (Bilanz page or Annual Electricity page)
    ▼
┌─────────────────────────────────────────┐
│  API Call: POST /api/balance-all/       │
│  Request body: { "action": "balance" }  │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  balance_all() view function            │
│  Initialize iteration counter = 0       │
└─────────────────────────────────────────┘
    │
    ▼
╔═══════════════════════════════════════════════════════════════╗
║                    ITERATION LOOP (Max 5)                     ║
╚═══════════════════════════════════════════════════════════════╝
    │
    │  ITERATION N (N = 1, 2, 3, 4, 5)
    ▼
┌─────────────────────────────────────────┐
│  Step 1: Calculate Current Balance      │
│  ─────────────────────────────────────  │
│  Total Supply = Sum(Renewable)          │
│  Total Demand = Sum(Verbrauch)          │
│  Imbalance = Supply - Demand            │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Step 2: Check Convergence              │
│  ─────────────────────────────────────  │
│  If |Imbalance| < 1% of Demand:         │
│      → CONVERGED, exit loop             │
│  Else:                                  │
│      → Continue to adjustment           │
└─────────────────────────────────────────┘
    │
    │  Not converged
    ▼
┌─────────────────────────────────────────┐
│  Step 3: Calculate Adjustments          │
│  ─────────────────────────────────────  │
│  WS_Electricity_Adj = Imbalance × 0.7   │
│  WS_Heat_Adj = Imbalance × 0.3          │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Step 4: Update WS Storage Values       │
│  ─────────────────────────────────────  │
│  9.3.1 (WS Electricity) += WS_Elec_Adj  │
│  9.3.4 (WS Heat) += WS_Heat_Adj         │
│  Save to database                       │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Step 5: Recalculate WS Formulas        │
│  ─────────────────────────────────────  │
│  recalculate_ws_data()                  │
│  • 365 days × 21 formulas/day           │
│  • FormulaVariable resolution           │
│  • Update row 366 (annual reference)    │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Step 6: Update Dependent Values        │
│  ─────────────────────────────────────  │
│  Renewable hierarchy recalculation      │
│  Verbrauch dependent fields update      │
│  Bilanz Aktiva/Passiva recalculation    │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Step 7: Increment Counter              │
│  ─────────────────────────────────────  │
│  iteration_counter += 1                 │
│  Log iteration status                   │
└─────────────────────────────────────────┘
    │
    │  Loop back if iteration < 5 and not converged
    │
    ▼
╔═══════════════════════════════════════════════════════════════╗
║                      LOOP EXIT CONDITIONS                     ║
╚═══════════════════════════════════════════════════════════════╝
    │
    │  Condition 1: Converged (|Imbalance| < 1%)
    │  Condition 2: Max iterations reached (5)
    ▼
┌─────────────────────────────────────────┐
│  Generate Response                      │
│  ─────────────────────────────────────  │
│  {                                      │
│    "status": "success/partial",         │
│    "iterations": N,                     │
│    "final_imbalance": X.XX%,            │
│    "converged": true/false,             │
│    "ws_electricity": value,             │
│    "ws_heat": value                     │
│  }                                      │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  HTTP Response: JSON                    │
│  Status Code: 200 (success) or          │
│               500 (error)               │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  UI Update                              │
│  • Display iteration count              │
│  • Show convergence status              │
│  • Update balance sheet values          │
│  • Display success/warning message      │
└─────────────────────────────────────────┘
```

### Diagram 3: Unified Recalculation Chain

```
┌──────────────────────────────────────────────────────────────────────┐
│                   Unified Recalculation Chain Flow                    │
└──────────────────────────────────────────────────────────────────────┘

USER ACTION
    │
    │  Click "Unified Recalc" or "Full Recalc" button
    ▼
┌─────────────────────────────────────────────────────────┐
│  API Endpoint: /api/unified-recalc/ or                  │
│                /api/run-full-recalc/                    │
└─────────────────────────────────────────────────────────┘
    │
    ▼
╔══════════════════════════════════════════════════════════════╗
║              SEQUENTIAL RECALCULATION CHAIN                  ║
╚══════════════════════════════════════════════════════════════╝
    │
    ▼
┌──────────────────────────────────────────────────┐
│  STEP 1: Recalculate Renewable from Land Use    │
│  ──────────────────────────────────────────────  │
│  recalculate_renewable_status_from_landuse()     │
│  • Process all LU_2.x (Solar land)              │
│  • Process all LU_3.x (Wind land)               │
│  • Process all LU_6.x (Biomass land)            │
│  • Update 9.1.1, 9.1.2, 9.1.3, 9.1.4 (Solar)    │
│  • Update 9.2.1, 9.2.2 (Wind)                   │
│  • Update 9.6.1 (Biomass)                       │
│  Duration: ~500ms                                │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│  STEP 2: Recalculate Renewable Hierarchy        │
│  ──────────────────────────────────────────────  │
│  recalculate_renewable()                         │
│  • Bottom-up traversal                          │
│  • Calculate parent sums from children          │
│  • 9.1 = 9.1.1 + 9.1.2 + 9.1.3 + 9.1.4         │
│  • 9 = 9.1 + 9.2 + 9.3 + ... + 9.7             │
│  Duration: ~300ms                                │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│  STEP 3: Recalculate Verbrauch (Consumption)    │
│  ──────────────────────────────────────────────  │
│  recalculate_verbrauch()                         │
│  • Evaluate formulas via FormulaVariable        │
│  • Update calculated fields                     │
│  • Process hierarchical dependencies            │
│  Duration: ~400ms                                │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│  STEP 4: Recalculate WS Data (Hydrogen Storage) │
│  ──────────────────────────────────────────────  │
│  recalculate_ws_data()                           │
│  • Process 365 days sequentially                │
│  • Apply 21 formulas per day                    │
│  • Total: 7,692 formula evaluations             │
│  • Update row 366 (annual reference)            │
│  Duration: ~5-10 seconds                         │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│  STEP 5: Recalculate Balance Sheet (Optional)   │
│  ──────────────────────────────────────────────  │
│  recalculate_bilanz()                            │
│  • Sum Aktiva (supply side)                     │
│  • Sum Passiva (demand side)                    │
│  • Calculate imbalance                          │
│  Duration: ~200ms                                │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│  STEP 6: Verify Data Integrity                  │
│  ──────────────────────────────────────────────  │
│  • Check for calculation errors                 │
│  • Validate parent-child sums                   │
│  • Log any inconsistencies                      │
│  Duration: ~100ms                                │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│  Generate Response                               │
│  ──────────────────────────────────────────────  │
│  {                                               │
│    "status": "success",                          │
│    "total_duration": "6.5s",                     │
│    "steps_completed": [                          │
│      "renewable_from_landuse",                   │
│      "renewable_hierarchy",                      │
│      "verbrauch",                                │
│      "ws_data",                                  │
│      "balance"                                   │
│    ],                                            │
│    "records_updated": 8542                       │
│  }                                               │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│  HTTP Response & UI Update                       │
│  • Display success message                       │
│  • Show duration and step details               │
│  • Refresh all data grids                       │
│  • Enable user to continue                      │
└──────────────────────────────────────────────────┘

TOTAL DURATION: ~6-12 seconds (depending on data size)
```

---

## 3.8.4 Validation Rules and Constraints

### Input Validation Matrix

| Data Type | Validation Rule | Example | Action on Failure |
|-----------|----------------|---------|-------------------|
| **Land Use Percentage** | 3-point increase limit | Current: 10% → Max: 13% | Reject, show error, revert to max allowed |
| **Land Use Percentage** | Negative values rejected | -5% | Reject, show error message |
| **Land Use Percentage** | Maximum 100% | 150% | Reject, show error message |
| **Land Use Percentage** | Decreases unlimited | 50% → 5% | Accept |
| **Verbrauch User Input** | Must be user_editable=True | Edit formula field | Reject, field is read-only |
| **Verbrauch Percentage** | Range 0-100% | 250% | Reject, show error message |
| **Renewable Fixed Values** | 9.3.1, 9.3.4 not editable | Direct edit attempt | Reject, only balance algorithm can modify |
| **Formula Fields** | Read-only, calculated | Manual edit | Reject, show "calculated field" message |
| **Authentication** | Valid session required | No session token | HTTP 401, redirect to login |

### Business Logic Constraints

**Constraint 1: Land Use Total**
- Sum of all land use categories should not exceed available land
- System validates total allocation
- Warning shown if total approaches 100%

**Constraint 2: Renewable Energy Hierarchy**
- Parent value must equal sum of children
- Enforced through formula system
- Automatic recalculation maintains integrity

**Constraint 3: Balance Sheet Equality**
- Target: Supply (Aktiva) = Demand (Passiva)
- Imbalance tracked and displayed
- Balance algorithm minimizes difference

**Constraint 4: WS Storage Capacity**
- Physical limits on hydrogen storage
- Maximum capacity constraints (future enhancement)
- Currently unlimited in model

**Constraint 5: Temporal Consistency**
- Daily WS calculations follow sequential order
- Day N depends on Day N-1 (cumulative storage)
- Row 366 = sum(rows 1-365) for annual values

---

## 3.8.5 Error Handling and Recovery

### Error Categories

**Category 1: Validation Errors (HTTP 400)**
- **Cause**: User input violates validation rules
- **Detection**: Backend validation layer
- **Response**: Error message with details
- **Recovery**: User corrects input and resubmits

**Example Error Response:**
```json
{
    "status": "error",
    "error_type": "validation_error",
    "message": "Cannot increase land use by more than 3 percentage points",
    "details": {
        "current_value": 10.0,
        "requested_value": 14.0,
        "increase": 4.0,
        "max_allowed": 13.0
    },
    "suggestion": "Please increase gradually to maintain realistic land use changes"
}
```

**Category 2: Authentication Errors (HTTP 401/403)**
- **Cause**: Invalid or expired session
- **Detection**: Django authentication middleware
- **Response**: Redirect to login page
- **Recovery**: User logs in again

**Category 3: Calculation Errors (HTTP 500)**
- **Cause**: Formula evaluation failure, database error
- **Detection**: Exception handling in calculation functions
- **Response**: Error logged, generic error message to user
- **Recovery**: System administrator investigates logs

**Category 4: Balance Non-Convergence (HTTP 200, partial success)**
- **Cause**: Balance algorithm reaches max iterations without converging
- **Detection**: Iteration counter check
- **Response**: Partial result returned with warning
- **Recovery**: User may manually adjust values or retry

### Error Logging

All errors logged to Django log files with following structure:
- Timestamp
- Error level (WARNING, ERROR, CRITICAL)
- User ID and session
- Request details (endpoint, method, parameters)
- Stack trace (for exceptions)
- Context data (current data state)

### Recovery Mechanisms

**Mechanism 1: Baseline Restore**
- API endpoint: `/api/baseline/restore/`
- Restores database to previous known-good state
- Used for critical errors or data corruption

**Mechanism 2: Transaction Rollback**
- Database transactions ensure atomic operations
- Failed operations rolled back automatically
- Data integrity maintained

**Mechanism 3: Client-Side Retry**
- JavaScript retry logic for network failures
- Exponential backoff strategy
- Maximum 3 retry attempts

---

## 3.8.6 Performance Optimization

### Optimization Strategies

**Strategy 1: Selective Recalculation**
- Only recalculate affected fields on user input
- Dependency tree traversal identifies impacted nodes
- Avoids unnecessary full recalculation

**Strategy 2: Database Query Optimization**
- Django ORM select_related() for foreign keys
- Prefetch_related() for many-to-many relationships
- Bulk update operations for multiple records

**Strategy 3: Caching**
- Session-level caching of user data
- Browser localStorage for UI state persistence
- Redis caching for frequently accessed data (future enhancement)

**Strategy 4: Asynchronous Operations**
- Background task queue for long-running calculations (future enhancement)
- Currently: synchronous execution with progress indicators
- Future: Celery integration for WS calculations

### Performance Benchmarks

| Operation | Duration | Records Affected | Optimization Applied |
|-----------|----------|------------------|----------------------|
| Single LU update | ~100ms | 1 LU + 1-4 Renewable | Selective cascade |
| Renewable hierarchy recalc | ~300ms | ~50 Renewable records | Bottom-up traversal |
| Verbrauch recalculation | ~400ms | ~100 Verbrauch records | Formula batching |
| WS data recalculation | ~6-10s | 7,692 WS records | Sequential daily processing |
| Balance algorithm (1 iter) | ~2-3s | WS + Renewable + Verbrauch | Iterative convergence |
| Full system recalc | ~10-15s | ~8,500 total records | Sequential chain |

---

## 3.8.7 Session and State Management

### Session Persistence

**localStorage Implementation:**
- Scroll position saved on page navigation
- Form input values preserved during session
- Collapsed/expanded section states maintained
- Chart view preferences stored (Status vs. Ziel toggle)

**Example localStorage Structure:**
```javascript
{
    "landuse_scroll_position": 450,
    "renewable_collapsed_sections": ["9.4", "9.5"],
    "cockpit_chart_view": "ziel",
    "last_modified_field": "LU_2.1",
    "user_preferences": {
        "auto_recalc": true,
        "show_formulas": false
    }
}
```

### Baseline Snapshot System

**Purpose**: Create restore points for data recovery and testing

**API Endpoints:**
- POST `/api/baseline/create/` - Create new baseline
- POST `/api/baseline/restore/` - Restore from baseline
- GET `/api/baseline/info/` - View baseline metadata

**Baseline Metadata:**
```json
{
    "baseline_id": "baseline_20260113_153045",
    "timestamp": "2026-01-13T15:30:45Z",
    "created_by": "admin",
    "description": "Before major land use changes",
    "record_counts": {
        "landuse": 45,
        "renewable": 52,
        "verbrauch": 98,
        "ws_data": 7692
    },
    "file_size": "2.5 MB"
}
```

---

## 3.8.8 Required Materials for Thesis

### Screenshots to Include

**Screenshot 1: Land Use Workflow**
- **Location**: Land Use page (`/landuse/`)
- **Content**: 
  - Before state: LU_2.1 at 32.5%
  - User editing field to 35.0%
  - After state: Updated value and cascade effect visible
  - Highlight: Validation message if attempting 40.0% (exceeds 3-point limit)

**Screenshot 2: Balance Button Workflow**
- **Location**: Bilanz page (`/bilanz/`)
- **Content**:
  - Aktiva vs. Passiva comparison
  - Balance button highlighted
  - Imbalance indicator before balance
  - Success message after balance completion
  - Iteration count displayed

**Screenshot 3: Unified Recalc Execution**
- **Location**: Any data page with recalc button
- **Content**:
  - Button click initiation
  - Progress indicator during execution
  - Success message with duration
  - Data grid refresh showing updated values

**Screenshot 4: Cockpit Dashboard**
- **Location**: Cockpit page (`/cockpit/`)
- **Content**:
  - Chart.js pie chart showing renewable distribution
  - Status vs. Ziel toggle buttons
  - KPI cards with key metrics
  - Real-time data display

**Screenshot 5: Error Handling Example**
- **Location**: Land Use page
- **Content**:
  - Invalid input (e.g., 100% attempted increase)
  - Error message display (orange highlight)
  - Value reverted to maximum allowed
  - User-friendly error explanation

### Code Snippets to Include

**Code Snippet 1: Django Signal for Cascade Calculation**
```python@receiver(post_save, sender=LandUse)
def recalculate_renewable_status_from_landuse(sender, instance, **kwargs):
    """Auto-triggered when LandUse saved"""
    renewable_code = lu_to_renewable_mapping.get(instance.code)
    if renewable_code:
        # Calculate energy from land area
        area_ha = instance.get_actual_area()
        energy_mwh = calculate_energy_from_area(area_ha, renewable_code)
        
        # Update renewable data (triggers further cascade)
        renewable = RenewableData.objects.get(code=renewable_code)
        renewable.status = energy_mwh
        renewable.save()        @receiver(post_save, sender=LandUse)
        def recalculate_renewable_status_from_landuse(sender, instance, **kwargs):
            """Auto-triggered when LandUse saved"""
            renewable_code = lu_to_renewable_mapping.get(instance.code)
            if renewable_code:
                # Calculate energy from land area
                area_ha = instance.get_actual_area()
                energy_mwh = calculate_energy_from_area(area_ha, renewable_code)
                
                # Update renewable data (triggers further cascade)
                renewable = RenewableData.objects.get(code=renewable_code)
                renewable.status = energy_mwh
                renewable.save()
# File: simulator/signals.py
@receiver(post_save, sender=LandUse)
def recalculate_renewable_status_from_landuse(sender, instance, **kwargs):
    """
    Triggered automatically when LandUse is saved.
    Updates dependent RenewableData entries.
    """
    if not instance.code:
        return
    
    # Map LU codes to Renewable codes
    lu_to_renewable = {
        'LU_2.1': '9.1.1',  # Ground PV
        'LU_2.2': '9.1.2',  # Roof PV
        'LU_3.1': '9.2.1',  # Wind Onshore
        'LU_6.1': '9.6.1',  # Biomass
    }
    
    renewable_code = lu_to_renewable.get(instance.code)
    if renewable_code:
        # Calculate new renewable energy value from land use
        area_ha = instance.get_actual_area()
        energy_mwh = calculate_energy_from_area(area_ha, renewable_code)
        
        # Update RenewableData
        renewable = RenewableData.objects.get(code=renewable_code)
        renewable.status = energy_mwh
        renewable.save()
        
        # Trigger parent recalculation
        recalculate_renewable_hierarchy(renewable)
```

**Code Snippet 2: FormulaVariable Resolution**
```python
# File: simulator/formula_service.py
def resolve_formula(formula):
    """
    Resolves formula variables using FormulaVariable system.
    """
    expression = formula.expression
    variables = FormulaVariable.objects.filter(formula=formula)
    
    context = {}
    for var in variables:
        value = resolve_variable_value(var)
        context[var.variable_name] = value
    
    # Evaluate with restricted context
    try:
        result = eval(expression, {"__builtins__": {}}, context)
        return result
    except Exception as e:
        logger.error(f"Formula evaluation failed: {e}")
        return None
```

**Code Snippet 3: Balance Algorithm Core Logic**
```python
# File: simulator/views.py
def balance_all(request):
    """
    Iterative energy balance algorithm.
    """
    max_iterations = 5
    convergence_threshold = 0.01  # 1%
    
    for iteration in range(1, max_iterations + 1):
        # Calculate current balance
        total_supply = sum_renewable_supply()
        total_demand = sum_consumption_demand()
        imbalance = total_supply - total_demand
        
        # Check convergence
        imbalance_percent = abs(imbalance) / total_demand
        if imbalance_percent < convergence_threshold:
            return JsonResponse({
                "status": "success",
                "converged": True,
                "iterations": iteration,
                "final_imbalance": imbalance_percent
            })
        
        # Adjust WS storage
        adjust_ws_storage(imbalance)
        recalculate_ws_data()
    
    return JsonResponse({
        "status": "partial",
        "converged": False,
        "iterations": max_iterations
    })
```

**Code Snippet 4: Client-Side AJAX Request**
```javascript
// File: simulator/templates/simulator/landuse_list.html
function updateLandUsePercent(pk) {
    const newPercent = document.getElementById(`percent_${pk}`).value;
    
    fetch(`/landuse/${pk}/update_percent/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ new_percent: parseFloat(newPercent) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showSuccessMessage('Land use updated successfully');
            refreshDependentFields(data.affected_fields);
        } else {
            showErrorMessage(data.message);
            revertFieldValue(pk, data.previous_value);
        }
    })
    .catch(error => {
        console.error('Update failed:', error);
        showErrorMessage('Network error occurred');
    });
}
```

### Flow Diagrams Included

This document already contains three detailed flow diagrams:
1. **Land Use to Renewable Energy Flow** (Section 3.8.3)
2. **Balance Algorithm Workflow** (Section 3.8.3)
3. **Unified Recalculation Chain Flow** (Section 3.8.3)

Additional diagrams recommended:
- **Use Case Diagram**: User interactions with system
- **Entity Relationship Diagram**: Database schema visualization
- **Deployment Diagram**: System architecture and components

---

## 3.8.9 Testing and Validation

### Test Scenarios Executed

**Test Suite 1: End-to-End Workflow Tests (BB-E2E)**
- 4 test cases, 100% pass rate
- Tests: User edit cascade, Balance button workflow, Invalid input handling, Page refresh accuracy

**Test Suite 2: Balance Algorithm Tests (BB-BAL)**
- Convergence testing
- Iteration limit testing
- Edge case handling (zero values, negative imbalances)

**Test Suite 3: Input Validation Tests (BB-VAL)**
- 3-point limit enforcement
- Negative value rejection
- Percentage overflow prevention
- Data type validation

**Test Suite 4: Calculation Accuracy Tests (BB-CALC)**
- Formula evaluation correctness
- Hierarchical sum verification
- Cross-module synchronization validation

### Test Execution Results

All test results documented in:
- [BB_E2E_END_TO_END_WORKFLOW_TESTS.md](BB_E2E_END_TO_END_WORKFLOW_TESTS.md)
- [BB_BAL_BALANCE_ALGORITHM_TESTS.md](BB_BAL_BALANCE_ALGORITHM_TESTS.md)
- [BB_VAL_INPUT_VALIDATION_TESTS.md](BB_VAL_INPUT_VALIDATION_TESTS.md)
- [BB_CALC_CALCULATION_ACCURACY_TESTS.md](BB_CALC_CALCULATION_ACCURACY_TESTS.md)

---

## 3.8.10 Summary

The 100ProSim system implements a comprehensive workflow architecture that seamlessly integrates user input, validation, calculation cascades, and balance operations. The workflow design ensures:

1. **Data Integrity**: Multi-layer validation prevents invalid data entry
2. **Calculation Accuracy**: FormulaVariable system ensures correct dependency resolution
3. **Performance**: Selective recalculation optimizes response times
4. **User Experience**: Real-time feedback and clear error messages
5. **Scalability**: Modular architecture supports future enhancements
6. **Reliability**: Transaction management and baseline recovery ensure data safety

The end-to-end workflow, from user interaction to final system response, demonstrates the practical application of the theoretical concepts presented in previous sections, providing a complete picture of the 100ProSim operational model.

---

## References for Section 3.8

- Django Framework Documentation: https://docs.djangoproject.com/
- Chart.js Visualization Library: https://www.chartjs.org/
- RESTful API Design Principles
- Black-Box Testing Methodologies
- Software Engineering Best Practices for Web Applications

---

**Thesis Recommendation**: Include this section after Section 3.7 (System Interfaces) and before Section 4 (Implementation Details) or Chapter 5 (Testing and Validation). The workflow section bridges interface design with implementation, providing crucial context for understanding system operation.
