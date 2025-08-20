#!/bin/bash
"""
Auto-activate first admin user during startup
This script runs during container initialization to ensure there's always an admin user
"""

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! pg_isready -h postgres -p 5432 -U postgres -d openwebui; do
    echo "Database not ready, waiting 5 seconds..."
    sleep 5
done

echo "Database is ready. Checking for admin users..."

# Run the Python script to activate first admin
python3 /app/scripts/activate_first_admin.py --auto

echo "Admin user check complete."