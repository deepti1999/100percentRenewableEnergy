"""
Percentage Rebalancer Service

When a user changes one member of a percentage group (e.g., sector 1.2 from 34.7% to 38%),
this service automatically redistributes the remaining allocation proportionally among siblings.

Example: KLIK Sectors (1.1, 1.2, 1.3) must always sum to 100%
- User changes 1.2: 34.7% → 38%
- Remaining: 100% - 38% = 62%
- Original ratio of others: 1.1=18.6%, 1.3=46.7% → combined = 65.3%
- New 1.1: 62% × (18.6 / 65.3) = 17.66%
- New 1.3: 62% × (46.7 / 65.3) = 44.34%
- Total: 38% + 17.66% + 44.34% = 100% ✅
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP


# Define percentage groups that must sum to 100%
# Each group has: name, parent_code, list of sibling codes
PERCENTAGE_GROUPS = [
    {
        "name": "KLIK Sectors",
        "parent_code": "1.0",  # Updated from 1.1 → 1.0 (Bedarfsniveau)
        "member_codes": ["1.1", "1.2", "1.3"],  # Updated: 1.1.1 → 1.1 (davon Haushalte)
        "target_sum": 100.0,
    },
]


def get_percentage_group(code: str) -> Optional[dict]:
    """
    Check if a code belongs to a percentage group.
    Returns the group definition or None.
    """
    for group in PERCENTAGE_GROUPS:
        if code in group["member_codes"]:
            return group
    return None


def rebalance_percentage_group(
    changed_code: str, 
    new_value: float,
    skip_codes: Optional[List[str]] = None
) -> Dict[str, float]:
    """
    After a user changes one member of a percentage group,
    redistribute the remaining allocation proportionally among siblings.
    
    Args:
        changed_code: The code that was changed by the user
        new_value: The new value set by the user
        skip_codes: Optional list of codes to skip (already in cascade)
    
    Returns:
        dict mapping code -> new_value for all rebalanced items (excluding the changed one)
    """
    from simulator.models import VerbrauchData
    
    # Find which group this code belongs to
    group = get_percentage_group(changed_code)
    if not group:
        return {}  # Not part of a percentage group
    
    member_codes = group["member_codes"]
    target_sum = group["target_sum"]  # Usually 100.0
    
    # Get current values for all siblings
    siblings = {}
    for code in member_codes:
        try:
            item = VerbrauchData.objects.get(code=code)
            # Use ziel (target) for percentage calculations
            siblings[code] = item.ziel or 0.0
        except VerbrauchData.DoesNotExist:
            siblings[code] = 0.0
    
    # Calculate remaining allocation after the changed value
    remaining = target_sum - new_value
    
    if remaining < 0:
        print(f"⚠️ Warning: {changed_code} = {new_value}% exceeds {target_sum}%")
        remaining = 0
    
    # Calculate the sum of siblings (excluding the changed one)
    other_codes = [c for c in member_codes if c != changed_code]
    other_sum = sum(siblings[c] for c in other_codes)
    
    # Redistribute proportionally
    result = {}
    
    if other_sum > 0:
        # Proportional redistribution
        for code in other_codes:
            old_value = siblings[code]
            proportion = old_value / other_sum
            new_sibling_value = remaining * proportion
            # Round to 2 decimal places
            new_sibling_value = round(new_sibling_value, 2)
            result[code] = new_sibling_value
    else:
        # Edge case: all other siblings are 0, distribute evenly
        count = len(other_codes)
        if count > 0:
            even_share = round(remaining / count, 2)
            for code in other_codes:
                result[code] = even_share
    
    # Verify total (handle rounding errors)
    total = new_value + sum(result.values())
    if abs(total - target_sum) > 0.01:
        # Adjust the last sibling to fix rounding error
        if other_codes:
            last_code = other_codes[-1]
            adjustment = target_sum - new_value - sum(result[c] for c in other_codes[:-1])
            result[last_code] = round(adjustment, 2)
    
    print(f"🔄 Rebalanced percentage group '{group['name']}':")
    print(f"   Changed: {changed_code} = {new_value}%")
    for code, val in result.items():
        print(f"   Adjusted: {code} = {val}%")
    print(f"   Total: {new_value + sum(result.values())}%")
    
    return result


def apply_rebalanced_percentages(
    changed_code: str,
    new_value: float,
    save_changes: bool = True
) -> Dict[str, dict]:
    """
    Calculate and optionally apply the rebalanced percentages to the database.
    
    Args:
        changed_code: The code that was changed
        new_value: The new percentage value
        save_changes: If True, save changes to database
    
    Returns:
        dict with format: {code: {"old": old_value, "new": new_value, "changed": bool}}
    """
    from simulator.models import VerbrauchData
    
    # Calculate rebalanced values
    rebalanced = rebalance_percentage_group(changed_code, new_value)
    
    if not rebalanced:
        return {changed_code: {"old": None, "new": new_value, "changed": True}}
    
    result = {}
    
    # Apply changes to database
    if save_changes:
        for code, value in rebalanced.items():
            try:
                item = VerbrauchData.objects.get(code=code)
                old_value = item.ziel
                
                # Update both user_percent and ziel
                item.user_percent = value
                item.ziel = value
                
                # Save without triggering another rebalance (skip_rebalance flag)
                item.save(skip_cascade=True, skip_rebalance=True)
                
                result[code] = {
                    "old": old_value,
                    "new": value,
                    "changed": abs((old_value or 0) - value) > 0.001
                }
                
                print(f"   ✅ {code}: {old_value}% → {value}%")
            except VerbrauchData.DoesNotExist:
                print(f"   ❌ {code}: Not found in database")
                result[code] = {"old": None, "new": value, "changed": True, "error": "Not found"}
    
    # Add the originally changed code
    result[changed_code] = {"old": None, "new": new_value, "changed": True, "is_primary": True}
    
    return result



def rebalance_if_in_group(code: str, new_value: float) -> bool:
    """
    Check if a code is in a percentage group and trigger rebalancing if so.
    Called from signals or save hooks.
    
    Args:
        code: The code that was changed
        new_value: The new value
    
    Returns:
        True if rebalancing was triggered, False otherwise
    """
    group = get_percentage_group(code)
    if not group:
        return False
    
    # Apply rebalancing
    apply_rebalanced_percentages(code, new_value, save_changes=True)
    return True
