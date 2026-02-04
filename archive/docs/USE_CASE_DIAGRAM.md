# Use Case Diagram - Energy Simulation Web Application

## System: Energy Simulation and Analysis Platform

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ENERGY SIMULATION WEB APPLICATION                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│                                                                               │
│    ┌──────────┐                                                              │
│    │          │                                                              │
│    │  Public  │──────────── View Renewable Energy Data                      │
│    │  User    │                    │                                        │
│    │          │                    ├─► Toggle Section 10 Details            │
│    │          │                    ├─► View Hierarchical Structure          │
│    │          │                    ├─► See Status/Target Values             │
│    │          │                    └─► Export to Excel                      │
│    │          │                                                              │
│    │          │──────────── View Energy Consumption (Verbrauch)             │
│    │          │                    │                                        │
│    │          │                    ├─► Browse Consumption Hierarchy         │
│    │          │                    ├─► See Calculated Values                │
│    │          │                    └─► Export Data                          │
│    │          │                                                              │
│    │          │──────────── View Land Use Data (Flächennutzung)             │
│    │          │                    │                                        │
│    │          │                    ├─► View Land Categories                 │
│    │          │                    ├─► See Status/Target Hectares           │
│    │          │                    └─► Download Report                      │
│    │          │                                                              │
│    │          │──────────── View SMARD Energy Data                          │
│    │          │                    │                                        │
│    │          │                    ├─► View Historical Solar Data (2023)    │
│    │          │                    ├─► View Historical Wind Data (2023)     │
│    │          │                    ├─► View Hydro Power Data                │
│    │          │                    ├─► View Electricity Demand              │
│    │          │                    └─► Analyze Daily Trends                 │
│    │          │                                                              │
│    │          │──────────── View Grundstoff & Synthetisierung               │
│    │          │                    │                                        │
│    │          │                    ├─► View Material Production Data        │
│    │          │                    └─► See Chemical Processes               │
│    │          │                                                              │
│    │          │──────────── View Mobile Applications (Luftverkehr)          │
│    │          │                    │                                        │
│    │          │                    └─► View Aviation Energy Data            │
│    │          │                                                              │
│    │          │──────────── View Stromwandlung (Power Conversion)           │
│    │          │                    │                                        │
│    │          │                    └─► View Energy Conversion Data          │
│    │          │                                                              │
│    │          │                                                              │
│    └──────────┘                                                              │
│                                                                               │
│                                                                               │
│    ┌──────────┐                                                              │
│    │          │                                                              │
│    │  Admin/  │──────────── Manage User Inputs ⭐ [PLANNED]                 │
│    │ Analyst  │                    │                                        │
│    │  User    │                    ├─► Create New Scenario                  │
│    │          │                    ├─► Edit Status Values                   │
│    │          │                    ├─► Edit Target Values                   │
│    │          │                    ├─► Modify Formulas                      │
│    │          │                    ├─► Save Custom Scenarios                │
│    │          │                    └─► Compare Scenarios                    │
│    │          │                                                              │
│    │          │──────────── View Bilanz (Balance Sheet) ⭐ [PLANNED]        │
│    │          │                    │                                        │
│    │          │                    ├─► View Energy Balance Summary          │
│    │          │                    ├─► Compare Supply vs Demand             │
│    │          │                    ├─► View Renewable Contribution %        │
│    │          │                    ├─► See Deficit/Surplus Analysis         │
│    │          │                    ├─► Generate Balance Report              │
│    │          │                    └─► Export Bilanz as PDF                 │
│    │          │                                                              │
│    │          │──────────── Import Data from CSV                            │
│    │          │                    │                                        │
│    │          │                    ├─► Import Renewable Energy Data         │
│    │          │                    ├─► Import Consumption Data              │
│    │          │                    ├─► Import Land Use Data                 │
│    │          │                    ├─► Import SMARD Historical Data         │
│    │          │                    └─► Validate Imported Data               │
│    │          │                                                              │
│    │          │──────────── Run Calculations & Simulations                  │
│    │          │                    │                                        │
│    │          │                    ├─► Recalculate All Formulas             │
│    │          │                    ├─► Run PyPSA Energy Distribution        │
│    │          │                    ├─► Calculate Section 10 Values          │
│    │          │                    ├─► Fix Formula Errors                   │
│    │          │                    └─► Validate Data Integrity              │
│    │          │                                                              │
│    │          │──────────── Manage Database                                 │
│    │          │                    │                                        │
│    │          │                    ├─► Access Django Admin                  │
│    │          │                    ├─► Create Test Users                    │
│    │          │                    ├─► Backup Database                      │
│    │          │                    └─► Restore Database                     │
│    │          │                                                              │
│    └──────────┘                                                              │
│                                                                               │
│                                                                               │
│    ┌──────────┐                                                              │
│    │          │                                                              │
│    │ System   │──────────── Auto-Calculate Formulas                         │
│    │ Backend  │                    │                                        │
│    │          │                    ├─► Evaluate Renewable Formulas          │
│    │          │                    ├─► Calculate Verbrauch Values           │
│    │          │                    ├─► Handle Percentage Conversions        │
│    │          │                    ├─► Resolve Code References              │
│    │          │                    └─► Return Calculated Results            │
│    │          │                                                              │
│    │          │──────────── Process Data Relationships                      │
│    │          │                    │                                        │
│    │          │                    ├─► Link Parent-Child Codes              │
│    │          │                    ├─► Handle Cross-Sheet References        │
│    │          │                    ├─► Validate Data Dependencies           │
│    │          │                    └─► Manage Calculation Cache             │
│    │          │                                                              │
│    │          │──────────── Generate Reports & Exports                      │
│    │          │                    │                                        │
│    │          │                    ├─► Generate Excel Files                 │
│    │          │                    ├─► Create CSV Exports                   │
│    │          │                    ├─► Format Data for Display              │
│    │          │                    └─► Render Charts & Graphs               │
│    │          │                                                              │
│    └──────────┘                                                              │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Use Case Descriptions

### 1. **View Renewable Energy Data**
- **Actor:** Public User
- **Description:** Browse hierarchical renewable energy sources with status and target values
- **Features:**
  - Toggle to show/hide sections 1-9
  - Section 10 (Endenergieangebot) shown by default
  - Color-coded categories
  - Export functionality

### 2. **View Energy Consumption (Verbrauch)**
- **Actor:** Public User
- **Description:** View energy consumption data across different sectors
- **Features:**
  - Hierarchical navigation
  - Calculated values based on formulas
  - Status vs Target comparison

### 3. **View SMARD Energy Data**
- **Actor:** Public User
- **Description:** Analyze historical energy production data from SMARD
- **Features:**
  - Daily data for 2023
  - Solar, Wind, Hydro, and Demand visualization
  - Interactive Chart.js graphs
  - Statistical summaries

### 4. **View Land Use Data (Flächennutzung)**
- **Actor:** Public User
- **Description:** View land usage categories and areas
- **Features:**
  - Land categories in hectares
  - Status vs Target land use
  - Export reports

### 5. **View Bilanz (Balance Sheet)** ⭐ **[PLANNED]**
- **Actor:** Admin/Analyst User
- **Description:** View comprehensive energy balance analysis
- **Features:**
  - Total renewable energy supply
  - Total energy demand
  - Supply-demand gap analysis
  - Renewable energy percentage contribution
  - Deficit/surplus calculations
  - Scenario comparison
  - PDF export of balance sheet

### 6. **Manage User Inputs** ⭐ **[PLANNED]**
- **Actor:** Admin/Analyst User
- **Description:** Allow users to input custom values and create scenarios
- **Features:**
  - Create new scenarios
  - Edit status/target values for any code
  - Modify formulas
  - Save multiple scenarios
  - Compare scenarios side-by-side
  - Reset to default values
  - Validate user inputs

### 7. **Import Data from CSV**
- **Actor:** Admin User
- **Description:** Import data files to populate database
- **Features:**
  - Import renewable energy hierarchies
  - Import consumption data
  - Import land use data
  - Import SMARD historical data
  - Validation and error checking

### 8. **Run Calculations & Simulations**
- **Actor:** Admin User
- **Description:** Execute calculation scripts and simulations
- **Features:**
  - Recalculate all formulas
  - Run PyPSA distribution models
  - Fix formula errors
  - Validate data integrity

### 9. **Auto-Calculate Formulas**
- **Actor:** System Backend
- **Description:** Automatically evaluate formulas when data is requested
- **Features:**
  - Parse formula expressions
  - Resolve code references
  - Handle percentage conversions
  - Return calculated values

### 10. **Process Data Relationships**
- **Actor:** System Backend
- **Description:** Manage relationships between data entities
- **Features:**
  - Parent-child code linking
  - Cross-sheet references
  - Dependency validation
  - Calculation caching

---

## Actor Descriptions

### 🧑 **Public User**
- Views all energy data
- Exports reports
- Analyzes trends
- No edit permissions

### 👨‍💼 **Admin/Analyst User** (Extends Public User)
- All Public User capabilities
- Can input custom values ⭐
- Can create scenarios ⭐
- Can view balance sheet ⭐
- Can import data
- Can run calculations
- Can manage database

### 🖥️ **System Backend**
- Automatic formula calculation
- Data validation
- Report generation
- Relationship management

---

## System Boundaries

### **Current Features (Implemented)**
- ✅ View Renewable Energy Data
- ✅ View Energy Consumption
- ✅ View Land Use Data
- ✅ View SMARD Data
- ✅ Import CSV Data
- ✅ Auto-Calculate Formulas
- ✅ Export to Excel
- ✅ Admin Dashboard

### **Planned Features** ⭐
- 🔜 **Bilanz (Balance Sheet)** - Energy balance analysis
- 🔜 **User Input Management** - Custom scenario creation
- 🔜 **Scenario Comparison** - Compare multiple scenarios
- 🔜 **PDF Export** - Generate PDF reports
- 🔜 **User Authentication** - Login/logout system
- 🔜 **Role-Based Access** - Public vs Admin permissions

---

## Use Case Relationships

### **Include Relationships:**
- "View Renewable Energy Data" includes "Auto-Calculate Formulas"
- "View Energy Consumption" includes "Auto-Calculate Formulas"
- "Manage User Inputs" includes "Validate User Inputs"
- "View Bilanz" includes "Auto-Calculate Formulas"
- "View Bilanz" includes "Generate Balance Report"

### **Extend Relationships:**
- "Export to Excel" extends "View Renewable Energy Data"
- "Toggle Section Details" extends "View Renewable Energy Data"
- "Compare Scenarios" extends "Manage User Inputs"
- "Export Bilanz PDF" extends "View Bilanz"

---

## Future Enhancements

1. **Real-time Collaboration** - Multiple users editing scenarios simultaneously
2. **API Integration** - Fetch live SMARD data via API
3. **Advanced Visualizations** - 3D charts, heatmaps, geographical maps
4. **Machine Learning** - Predict future energy demands
5. **Mobile App** - iOS/Android companion apps
6. **Notifications** - Alert users when targets are not met
7. **Audit Trail** - Track all changes made to data

---

Generated: November 6, 2025
