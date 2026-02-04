"""
LandUse Calculator - Hierarchical land use calculations
======================================================

Handles:
- Parent-child relationships (LU_0 -> LU_1 -> LU_1.1, etc.)
- Automatic target_ha calculation from user_percent
- Automatic target_percent calculation from target_ha
- Cascade updates to children
- Priority: manual target_ha edits > automatic calculations
"""


class LandUseCalculator:
    """Calculator for hierarchical land use data"""
    
    @staticmethod
    def calculate_target_ha(parent_target_ha, user_percent):
        """
        Calculate target_ha from parent and user_percent.
        
        Args:
            parent_target_ha: Parent's target_ha value
            user_percent: User's percentage input
            
        Returns:
            float: Calculated target_ha
        """
        if parent_target_ha is None or user_percent is None:
            return None
        return parent_target_ha * (user_percent / 100.0)
    
    @staticmethod
    def calculate_target_percent(parent_target_ha, target_ha):
        """
        Calculate target_percent from target_ha and parent.
        
        Args:
            parent_target_ha: Parent's target_ha value
            target_ha: This item's target_ha value
            
        Returns:
            float: Calculated target_percent
        """
        if parent_target_ha is None or target_ha is None or parent_target_ha == 0:
            return None
        return (target_ha / parent_target_ha) * 100.0
    
    @staticmethod
    def should_cascade_to_children(target_ha_changed, target_ha_manually_changed):
        """
        Determine if changes should cascade to children.
        
        Cascade only if:
        - target_ha changed (from user_percent calculation)
        - AND target_ha was NOT manually edited
        
        This preserves manual edits while enabling automatic updates.
        
        Args:
            target_ha_changed: Boolean indicating if target_ha changed
            target_ha_manually_changed: Boolean indicating if target_ha was manually edited
            
        Returns:
            bool: True if should cascade, False otherwise
        """
        return target_ha_changed and not target_ha_manually_changed
    
    @staticmethod
    def get_parent_code(code):
        """
        Determine parent code from child code.
        
        Examples:
            LU_1.1 -> LU_1
            LU_2.2.1 -> LU_2.2
            LU_3 -> LU_0
            
        Args:
            code: The child code
            
        Returns:
            str or None: Parent code, or None if no parent
        """
        if not code or not code.startswith('LU_'):
            return None
        
        code_parts = code[3:].split('.')  # Remove "LU_" prefix
        
        if len(code_parts) == 1:
            # Top level (e.g., LU_1 -> LU_0)
            return 'LU_0'
        else:
            # Multi-level (e.g., LU_1.1 -> LU_1)
            parent_parts = code_parts[:-1]
            return 'LU_' + '.'.join(parent_parts)
