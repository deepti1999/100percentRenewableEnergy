# Land Use Validation Feature

## Overview
This feature prevents users from making unrealistic land use increases by implementing a configurable maximum increase percentage.

## How It Works

### Default Behavior
- **Maximum Increase**: 3 percentage points
- **Example**: If current land use is 10%, maximum allowed is 13% (10% + 3 percentage points = 13%)
- **Another Example**: If current is 20%, maximum allowed is 23% (20% + 3 = 23%)

### Validation Rules
1. ✅ **Decreases**: Always allowed (no limit on reducing land use)
2. ✅ **Starting from 0%**: Any value up to 100% is allowed
3. ✅ **Within limit**: Increases up to MAX_INCREASE_PERCENT percentage points are accepted
4. ❌ **Exceeds limit**: Increases beyond MAX_INCREASE_PERCENT percentage points are rejected

## Configuration

### To Change the Maximum Increase Percentage:

Edit `landuse_project/settings.py`:

```python
# Land Use Validation Settings
LANDUSE_MAX_INCREASE_PERCENT = 300  # Change this value
```

**Common values:**
- `3` = Maximum 3 percentage points (10% → max 13%) [DEFAULT]
- `5` = Maximum 5 percentage points (10% → max 15%)
- `10` = Maximum 10 percentage points (10% → max 20%)
- `20` = Maximum 20 percentage points (10% → max 30%)
- `50` = Maximum 50 percentage points (10% → max 60%)

## User Experience

### When Validation Fails:

**Error Message Shown:**
```
⚠️ Cannot increase land use by more than 3 percentage points.

Current: 10.00%
Requested: 14.00%
Increase: 4.00 percentage points
Maximum allowed: 13.00%

Please increase gradually to maintain realistic land use changes.
```

**Behavior:**
1. Error message displayed to user
2. Input field automatically reverted to maximum allowed value
3. Field highlighted in orange for 3 seconds
4. No database changes made
5. User can try again with a lower value

## Testing

### Manual Test:
```bash
# Start the server
python manage.py runserver

# Open browser: http://127.0.0.1:8000/landuse/

# Try to change a land use value:
# - Current: 10%
# - Try entering: 50%
# - Expected: Error message appears, value reverts to 40%
```

### Automated Test:
```bash
# Run validation test
python test_landuse_validation.py
```

## Technical Details

### Backend Validation
**File**: `simulator/views.py`
**Function**: `update_landuse_percent(request, pk)`

```python
# Validation logic
MAX_INCREASE_PERCENT = getattr(settings, 'LANDUSE_MAX_INCREASE_PERCENT', 3)
current_percent = landuse.user_percent or 0

if current_percent > 0:
    percent_change = ((new_percent - current_percent) / current_percent) * 100
    if percent_change > MAX_INCREASE_PERCENT:
        # Reject and return error
```

### Frontend Handling
**File**: `simulator/templates/simulator/landuse_list.html`
**Function**: `updateLandUsePercent(pk)`

```javascript
// Handle validation error
if (data.status === "error") {
    showMessage(errorMsg, 'danger');
    
    // Revert to safe value
    if (data.max_allowed_value) {
        inputField.value = data.max_allowed_value.toFixed(2);
        // Highlight field
    }
}
```

## Benefits

1. **Prevents Data Entry Errors**: Users can't accidentally enter extreme values
2. **Maintains Realism**: Land use changes stay within reasonable bounds
3. **User-Friendly**: Clear error messages explain what went wrong
4. **Flexible**: Administrators can adjust limits via settings
5. **Safe**: No data corruption - invalid changes are rejected
6. **Smooth UX**: Input auto-reverts to safe value, user can continue working

## Examples

### Example 1: Small Increase (Allowed)
- Current: 10%
- New: 12%
- Change: +2 percentage points
- Result: ✅ **ALLOWED** (within 3 point limit)

### Example 2: At the Limit (Allowed)
- Current: 10%
- New: 13%
- Change: +3 percentage points
- Result: ✅ **ALLOWED** (exactly at 3 point limit)

### Example 3: Over Limit (Blocked)
- Current: 10%
- New: 14%
- Change: +4 percentage points
- Result: ❌ **BLOCKED** (exceeds 3 point limit)
- Maximum allowed: 13%

### Example 4: Starting from Zero (Always Allowed)
- Current: 0%
- New: 50%
- Change: N/A (starting from zero)
- Result: ✅ **ALLOWED** (special case)

### Example 5: Decrease (Always Allowed)
- Current: 50%
- New: 10%
- Change: -80%
- Result: ✅ **ALLOWED** (decreases have no limit)

## Customization for Different Use Cases

### Conservative Approach (Very Strict - CURRENT DEFAULT):
```python
LANDUSE_MAX_INCREASE_PERCENT = 3  # Only 3% increase allowed
```
Use for: Production environments, strict data governance, preventing errors

### Slightly More Flexible:
```python
LANDUSE_MAX_INCREASE_PERCENT = 10  # 10% increase allowed
```
Use for: Testing with some freedom, gradual changes

### Moderate Approach (Balanced):
```python
LANDUSE_MAX_INCREASE_PERCENT = 50  # 50% increase allowed
```
Use for: Development, scenarios, moderate flexibility

### Disable Validation:
```python
LANDUSE_MAX_INCREASE_PERCENT = 999999  # Effectively unlimited
```
Use for: Testing, migration, special cases

## Future Enhancements

Potential improvements:
1. Different limits for different land use categories
2. Time-based limits (daily/weekly maximum changes)
3. User role-based limits (admin vs regular user)
4. Audit log of rejected changes
5. Email notifications for attempted excessive changes
