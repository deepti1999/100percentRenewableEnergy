# Energy Simulation Project

A Django-based energy simulation and analysis platform for renewable energy planning and consumption tracking.

## Features

- **Land Use Management**: Track and manage land use data for renewable energy installations
- **Renewable Energy Data**: Comprehensive renewable energy data management with hierarchical structure
- **Energy Consumption (Verbrauch)**: Track and calculate energy consumption across different sectors
- **SMARD Data Analysis**: Visualize historical energy generation data from SMARD (2023)
- **Bilanz (Balance Sheet)**: Compare renewable and fossil energy supply with demand
- **Cockpit Dashboard**: Overview of key energy metrics and statistics
- **Annual Electricity**: Track annual electricity generation and consumption

## Project Structure

```
check/
├── landuse_project/        # Django project settings
├── simulator/              # Main application
│   ├── templates/          # HTML templates
│   ├── management/         # Django management commands
│   ├── migrations/         # Database migrations
│   ├── models.py           # Data models
│   ├── views.py            # View functions
│   └── urls.py             # URL routing
├── data/                   # CSV data files
├── manage.py               # Django management script
└── db.sqlite3              # SQLite database
```

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd check
```

2. Install dependencies:
```bash
pip install django pandas numpy
```

3. Run migrations:
```bash
python3 manage.py migrate
```

4. Create a superuser:
```bash
python3 manage.py createsuperuser
```

5. Run the development server:
```bash
python3 manage.py runserver
```

6. Access the application at `http://127.0.0.1:8000/`

## Data Models

### LandUse
- Tracks land usage for renewable energy installations
- Fields: code, name, category, status (hectares), ziel (target)

### RenewableData
- Hierarchical renewable energy data structure
- Fields: code, name, unit, status, ziel, formula, parent_code

### VerbrauchData
- Energy consumption data across sectors
- Fields: code, name, unit, status, ziel, formula, is_calculated

### GebaeudewaermeData
- Building heat consumption data
- Fields: code, name, unit, status, ziel

## Key Features

### Renewable Energy Page
- Hierarchical display of renewable energy sources
- Section 10 highlighted with main categories in blue
- Show/hide detailed sections for better navigation

### SMARD Analysis
- Historical energy generation data visualization (2023)
- Solar, Wind, and Hydro generation tracking
- Demand comparison with actual consumption data

### Bilanz (Balance Sheet)
- Renewable vs Fossil fuel breakdown
- Gebäudewärme (Building Heat) with Abwärme calculations
- Prozesswärme (Process Heat) tracking
- Status vs Ziel (Target) comparison

## Technologies Used

- **Backend**: Django 4.2
- **Database**: SQLite
- **Frontend**: HTML, CSS, Bootstrap
- **Charts**: Chart.js
- **Data Processing**: Pandas, NumPy

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is for educational and research purposes.

## Contact

Deepti Maheedharan
