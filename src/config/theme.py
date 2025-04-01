"""Theme colors and styles configuration"""

# Theme colors
PRIMARY = "#1f77b4"    # Blue
SECONDARY = "#2ca02c"  # Green
ACCENT = "#ff7f0e"     # Orange
TEXT = "#2c3e50"       # Dark blue-gray

# Custom CSS theme
CUSTOM_CSS = f"""
<style>
.main {{ color: {TEXT}; }}
.stButton button {{ background: {PRIMARY}; color: white; }}
.stProgress .st-bo {{ background: {SECONDARY}; }}
.stAlert {{ border-left: 2px solid {ACCENT}; }}
.stSuccess {{ border-color: {SECONDARY}; }}
.stWarning {{ border-color: {ACCENT}; }}
</style>
"""