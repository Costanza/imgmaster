#!/usr/bin/env python3

from collections import defaultdict
from datetime import datetime

def test_sort_function():
    """Test the sort function logic directly."""
    
    # Simulate group dates like our function would create
    group_dates = {
        'later': datetime(2022, 6, 15, 14, 30, 0),     # Later date
        'earlier': datetime(2022, 1, 10, 9, 15, 0),   # Earlier date  
        'middle': datetime(2022, 3, 20, 11, 45, 0),   # Middle date
        'no_date_z': None,                             # No date (z sorts last)
        'no_date_a': None,                             # No date (a sorts first)
    }
    
    # This is the same sort key function used in rename_service.py
    def sort_key(group_name):
        date = group_dates[group_name]
        return (date is None, date if date else datetime.min)
    
    sorted_groups = sorted(group_dates.keys(), key=sort_key)
    
    print("Groups sorted chronologically:")
    for i, group_name in enumerate(sorted_groups, 1):
        date = group_dates[group_name]
        date_str = date.strftime('%Y-%m-%d %H:%M:%S') if date else 'No date'
        print(f"  {i:03d}: {group_name} ({date_str})")
    
    # Expected order:
    # 1. earlier (2022-01-10) - earliest date gets sequence 001
    # 2. middle (2022-03-20)  - middle date gets sequence 002 
    # 3. later (2022-06-15)   - latest date gets sequence 003
    # 4. Groups without dates maintain their original order (stable sort)
    
    # Check that chronological ordering works for groups with dates
    groups_with_dates = [g for g in sorted_groups if group_dates[g] is not None]
    expected_with_dates = ['earlier', 'middle', 'later']
    
