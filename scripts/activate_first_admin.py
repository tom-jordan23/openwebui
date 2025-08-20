#!/usr/bin/env python3
"""
Activate First Admin User Script

This script ensures the first user account is automatically activated as an admin.
It should be run during initial setup or can be called manually.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_connection():
    """Get database connection from environment variables."""
    try:
        # Try to get database URL from environment
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            conn = psycopg2.connect(database_url)
        else:
            # Fallback to individual parameters
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'openwebui'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'postgres')
            )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def check_and_activate_first_admin(email=None):
    """Check if there's an admin user, and activate the first user if not."""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if there are any admin users
            cur.execute("SELECT COUNT(*) as admin_count FROM \"user\" WHERE role = 'admin';")
            admin_count = cur.fetchone()['admin_count']
            
            if admin_count > 0:
                logger.info(f"Found {admin_count} admin user(s). No action needed.")
                return True
            
            # Get the first user or specific email
            if email:
                cur.execute("""
                    SELECT u.id, u.name, u.email, u.role, a.active 
                    FROM "user" u 
                    JOIN auth a ON u.id = a.id 
                    WHERE u.email = %s;
                """, (email,))
            else:
                cur.execute("""
                    SELECT u.id, u.name, u.email, u.role, a.active 
                    FROM "user" u 
                    JOIN auth a ON u.id = a.id 
                    ORDER BY u.created_at ASC 
                    LIMIT 1;
                """)
            
            user = cur.fetchone()
            if not user:
                logger.warning("No users found in database.")
                return False
            
            # Activate user and set as admin
            if user['role'] != 'admin' or not user['active']:
                cur.execute("""
                    UPDATE "user" SET role = 'admin' WHERE id = %s;
                """, (user['id'],))
                
                cur.execute("""
                    UPDATE auth SET active = true WHERE id = %s;
                """, (user['id'],))
                
                conn.commit()
                logger.info(f"Successfully activated user {user['name']} ({user['email']}) as admin.")
                return True
            else:
                logger.info(f"User {user['name']} ({user['email']}) is already an active admin.")
                return True
                
    except Exception as e:
        logger.error(f"Error activating first admin: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def activate_specific_user(email, role='admin'):
    """Activate a specific user with the given role."""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if user exists
            cur.execute("""
                SELECT u.id, u.name, u.email, u.role, a.active 
                FROM "user" u 
                JOIN auth a ON u.id = a.id 
                WHERE u.email = %s;
            """, (email,))
            
            user = cur.fetchone()
            if not user:
                logger.error(f"User with email {email} not found.")
                return False
            
            # Update user role and activation status
            cur.execute("""
                UPDATE "user" SET role = %s WHERE id = %s;
            """, (role, user['id']))
            
            cur.execute("""
                UPDATE auth SET active = true WHERE id = %s;
            """, (user['id']))
            
            conn.commit()
            logger.info(f"Successfully activated user {user['name']} ({email}) with role '{role}'.")
            return True
            
    except Exception as e:
        logger.error(f"Error activating user {email}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def list_users():
    """List all users and their status."""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT u.id, u.name, u.email, u.role, a.active, u.created_at
                FROM "user" u 
                JOIN auth a ON u.id = a.id 
                ORDER BY u.created_at ASC;
            """)
            
            users = cur.fetchall()
            if not users:
                logger.info("No users found in database.")
                return True
            
            print("\nCurrent Users:")
            print("=" * 80)
            print(f"{'Name':<20} {'Email':<30} {'Role':<10} {'Active':<8} {'Created'}")
            print("-" * 80)
            
            for user in users:
                created_at = user['created_at'] if user['created_at'] else 'Unknown'
                print(f"{user['name']:<20} {user['email']:<30} {user['role']:<10} {user['active']:<8} {created_at}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return False
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Activate first admin user for OpenWebUI')
    parser.add_argument('--email', help='Specific email to activate')
    parser.add_argument('--role', default='admin', help='Role to assign (default: admin)')
    parser.add_argument('--list', action='store_true', help='List all users')
    parser.add_argument('--auto', action='store_true', help='Auto-activate first user as admin')
    
    args = parser.parse_args()
    
    if args.list:
        success = list_users()
    elif args.email:
        success = activate_specific_user(args.email, args.role)
    else:
        success = check_and_activate_first_admin(args.email)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()