#!/usr/bin/env python3
"""
Check Admin Access in OpenWebUI
This script helps identify available admin features and access methods.
"""

import requests
import json
from urllib.parse import urljoin

def check_admin_endpoints():
    """Check various admin endpoints to see what's available."""
    base_url = "http://localhost:3000"
    
    # Common admin endpoints to test
    endpoints = [
        "/api/v1/users",
        "/api/v1/auths/admin",
        "/api/v1/configs",
        "/api/admin/users",
        "/api/admin/config",
        "/workspace",
        "/admin",
        "/admin/panel",
        "/api/v1/models",
        "/api/v1/configs/default"
    ]
    
    print("🔍 Checking OpenWebUI Admin Endpoints")
    print("=" * 50)
    
    for endpoint in endpoints:
        url = urljoin(base_url, endpoint)
        try:
            response = requests.get(url, timeout=5)
            status = response.status_code
            
            if status == 200:
                print(f"✅ {endpoint} - ACCESSIBLE (200)")
                try:
                    data = response.json()
                    if isinstance(data, dict) and len(data) < 5:
                        print(f"   📄 Response: {json.dumps(data, indent=2)}")
                except:
                    print(f"   📄 Response: HTML/Text content")
            elif status == 401:
                print(f"🔐 {endpoint} - REQUIRES AUTH (401)")
            elif status == 403:
                print(f"❌ {endpoint} - FORBIDDEN (403)")
            elif status == 404:
                print(f"💭 {endpoint} - NOT FOUND (404)")
            else:
                print(f"❓ {endpoint} - STATUS {status}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - ERROR: {e}")
    
    print("\n🔍 Checking Frontend Routes")
    print("=" * 30)
    
    # Check if admin routes exist in the frontend
    frontend_routes = [
        "/workspace",
        "/admin", 
        "/admin/users",
        "/admin/models",
        "/admin/settings"
    ]
    
    for route in frontend_routes:
        url = urljoin(base_url, route)
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                content = response.text
                if "admin" in content.lower() or "workspace" in content.lower():
                    print(f"✅ {route} - FRONTEND ROUTE EXISTS")
                else:
                    print(f"📄 {route} - GENERIC PAGE")
            else:
                print(f"❌ {route} - STATUS {response.status_code}")
        except:
            print(f"❌ {route} - CONNECTION ERROR")

def check_user_status():
    """Check current user status in database."""
    print("\n👤 Current User Status")
    print("=" * 25)
    
    import os
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            database='openwebui',
            user='postgres',
            password='postgres'
        )
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT u.id, u.name, u.email, u.role, a.active, u.created_at
                FROM "user" u 
                JOIN auth a ON u.id = a.id 
                ORDER BY u.created_at ASC;
            """)
            
            users = cur.fetchall()
            
            for user in users:
                status = "🟢 ACTIVE" if user['active'] else "🔴 INACTIVE"
                role_icon = "👑" if user['role'] == 'admin' else "👤"
                print(f"{role_icon} {user['name']} ({user['email']})")
                print(f"   Role: {user['role']} | Status: {status}")
                print(f"   ID: {user['id']}")
                print()
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")

if __name__ == "__main__":
    check_admin_endpoints()
    check_user_status()
    
    print("\n💡 Next Steps:")
    print("1. Look for 'ACCESSIBLE' endpoints above")
    print("2. Try accessing /workspace or /admin URLs directly") 
    print("3. Check your browser's Network tab when logged in")
    print("4. Look for admin sections in the left sidebar after login")