# User Editable Fields Feature

## Overview
This feature allows administrators to control which VerbrauchData (Energy Consumption) fields are editable by users in the frontend.

## How It Works

### 1. Admin Interface
Administrators can mark any VerbrauchData field as user-editable in the Django Admin:

1. Go to **Admin → Simulator → Verbrauch data**
2. Find the field you want to make editable (e.g., 2.1.1 - Wohnfläche pro Person)
3. Check the **User editable** checkbox in the list view or detail view
4. Save the changes

### 2. Frontend Behavior
- **Editable fields**: Show with a light background and "Enter %..." placeholder, users can click and edit
- **Non-editable fields**: Show as read-only with gray text, users cannot edit

### 3. What Happens When User Edits
When a user edits an editable field:
1. The value is saved to the database
2. All dependent calculated fields are automatically recalculated
3. The entire page refreshes with updated values
4. Percentage groups automatically rebalance if applicable

## Default Configuration
By default, the following fields are set as user-editable:
- All fields with Unit = "%"
- Specific important fields like:
  - 2.1.1 (Wohnfläche pro Person - qm/Person)
  - 2.2, 2.4, 2.5, 2.7, 2.8, 2.9

## Using the Helper Script

### List All Editable Fields
```bash
python3 set_user_editable.py list
```

### Make a Field Editable
```bash
python3 set_user_editable.py 2.1.1 true
```

### Make a Field Non-Editable
```bash
python3 set_user_editable.py 2.1.1 false
```

## Examples

### Example 1: Make "Wohnfläche pro Person" (2.1.1) Editable
```bash
python3 set_user_editable.py 2.1.1 true
```

Output:
```
✅ ENABLED user editing for 2.1.1
   Code: 2.1.1
   Category: Wohnfläche pro Person
   Unit: qm/Person
   Previous: Not editable
   Current:  Editable

✓ Users can now edit this field in the frontend.
```

### Example 2: Disable Editing for a Percentage Field
```bash
python3 set_user_editable.py 2.4.2 false
```

## Technical Details

### Database Schema
The `user_editable` field is a boolean field in the VerbrauchData model:
- `user_editable = True`: Field is editable by users in frontend
- `user_editable = False`: Field is read-only in frontend

### Template Logic
In `verbrauch.html`, the template checks the `user_editable` flag:
```html
{% if row.user_editable %}
  <td contenteditable="true" class="bg-light text-center editable-user-input" ...>
    <!-- Editable cell -->
  </td>
{% else %}
  <td class="text-center text-muted">
    <!-- Read-only cell -->
  </td>
{% endif %}
```

### View Logic
The view passes the `user_editable` flag to the template along with other data:
```python
temp_data.append({
    'code': item.code,
    'category': item.category,
    'unit': item.unit,
    'status': display_status,
    'ziel': display_ziel,
    'user_percent': item.user_percent,
    'is_calculated': item.is_calculated,
    'user_editable': item.user_editable,  # Controls frontend editability
})
```

## Migration
The feature was added via Django migrations:
- Migration: `0035_remove_verbrauchdata_is_user_editable_and_more.py`
- Added field: `user_editable` (BooleanField, default=False)

## Benefits
1. **Flexible Control**: Admins decide which fields users can edit
2. **Unit-Agnostic**: Not limited to just "%" fields anymore
3. **Better UX**: Clear visual distinction between editable and read-only fields
4. **Easy Management**: Can be changed anytime via Admin UI or script
5. **Safe**: Read-only fields are protected from accidental user changes

## Notes
- Changes take effect immediately after saving in Admin
- No server restart required
- The feature works alongside existing calculation and cascade systems
- All edits trigger proper recalculation of dependent fields
