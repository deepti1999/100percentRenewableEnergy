from typing import List

def recalc_renewables_for_verbrauch(code: str) -> List[str]:
    """
    Recalculate RenewableData items whose formulas reference a given VerbrauchData code.
    Returns list of RenewableData codes updated.
    """
    from simulator.models import LandUse, RenewableData, VerbrauchData
    from calculation_engine.renewable_engine import RenewableCalculator

    dependents = RenewableData.objects.filter(
        is_fixed=False,
        formula__icontains=f"VerbrauchData_{code}",
    )
    if not dependents:
        return []

    # Prepare calculator with fresh data sources
    calculator = RenewableCalculator()
    landuse_data = {
        i.code: {'status_ha': i.status_ha or 0, 'target_ha': i.target_ha or 0}
        for i in LandUse.objects.all()
    }
    verbrauch_data = {
        i.code: {'status': i.status or 0, 'ziel': i.ziel or 0}
        for i in VerbrauchData.objects.all()
    }
    renewable_data = {
        i.code: {'status_value': i.status_value or 0, 'target_value': i.target_value or 0}
        for i in RenewableData.objects.all()
    }
    calculator.set_data_sources(landuse_data, verbrauch_data, renewable_data)

    updated: List[str] = []

    for item in dependents:
        try:
            # Use ONLY the database-driven calculator - no fallback to eval()
            calc_status, calc_target = calculator.calculate(item.code)
            
            # Only update if calculator successfully computed values
            if calc_status is not None and calc_target is not None:
                status_changed = abs((item.status_value or 0) - calc_status) > 0.01
                target_changed = abs((item.target_value or 0) - calc_target) > 0.01
                if status_changed or target_changed:
                    item.status_value = calc_status
                    item.target_value = calc_target
                    item.save()  # allow cascades
                    updated.append(item.code)
            else:
                # Calculator returned None - formula invalid or data missing
                print(f"ERROR: Cannot calculate {item.code} - check formula and data in database")
                
        except Exception as exc:  # pragma: no cover - defensive
            print(f"ERROR: Renewable recalc from Verbrauch {code} failed for {item.code}: {exc}")
    return updated
