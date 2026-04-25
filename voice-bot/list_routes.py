"""List all Flask routes"""
from app import app

print("Registered routes:")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint:30s} {str(rule.methods):30s} {rule.rule}")
