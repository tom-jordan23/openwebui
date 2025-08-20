# Admin User Setup Guide

This guide explains how admin user activation works and how to resolve common admin access issues.

## 🔧 Automatic Admin Activation

The platform now includes automatic admin activation to prevent the "Account Activation Pending" issue for the first user.

### How It Works

1. **Admin Activator Service**: A dedicated Docker service (`admin-activator`) runs during startup
2. **Database Check**: It checks if any admin users exist in the database
3. **Auto-Activation**: If no admin users are found, it automatically promotes the first registered user to admin
4. **Dependency Management**: The main application waits for this check to complete before starting

### Configuration

#### Environment Variables

Add these to your `.env` file:

```bash
# Auto-activate first user as admin
AUTO_ACTIVATE_FIRST_ADMIN=true

# Optional: Specify which email should be admin
DEFAULT_ADMIN_EMAIL=your-email@domain.com
```

#### Docker Compose Integration

The `admin-activator` service is automatically included in `docker-compose.yml`:

```yaml
admin-activator:
  image: postgres:15-alpine
  container_name: admin-activator
  environment:
    - PGPASSWORD=postgres
  depends_on:
    - postgres
  command: >
    # Automatic admin activation logic
  networks:
    - ai-assistant
  restart: "no"
```

## 🚨 Manual Admin Activation

If you need to manually activate an admin user, use these methods:

### Method 1: Using the Activation Script

```bash
# Activate first user as admin
python3 scripts/activate_first_admin.py --auto

# Activate specific user
python3 scripts/activate_first_admin.py --email user@domain.com

# List all users and their status
python3 scripts/activate_first_admin.py --list
```

### Method 2: Direct Database Access

```bash
# Connect to database
docker compose exec postgres psql -U postgres -d openwebui

# Check current users
SELECT u.id, u.name, u.email, u.role, a.active 
FROM "user" u 
JOIN auth a ON u.id = a.id;

# Activate specific user as admin
UPDATE "user" SET role = 'admin' WHERE email = 'your-email@domain.com';
UPDATE auth SET active = true WHERE id = (
    SELECT id FROM "user" WHERE email = 'your-email@domain.com'
);

# Verify the change
SELECT u.id, u.name, u.email, u.role, a.active 
FROM "user" u 
JOIN auth a ON u.id = a.id 
WHERE u.email = 'your-email@domain.com';
```

### Method 3: Using Docker Compose Restart

If auto-activation is enabled, simply restart the services:

```bash
# Restart the admin activator service
docker compose restart admin-activator

# Check logs to see activation results
docker compose logs admin-activator
```

## 🔍 Troubleshooting

### Issue: "Account Activation Pending" Message

**Solution 1: Check Auto-Activation Status**
```bash
# Check if admin activator ran successfully
docker compose logs admin-activator

# Expected output should show:
# "Successfully activated first user as admin: [User Name] | [Email]"
```

**Solution 2: Manual Activation**
```bash
# Use the activation script
python3 scripts/activate_first_admin.py --email your-email@domain.com
```

**Solution 3: Database Direct Fix**
```bash
# Quick database fix
docker compose exec postgres psql -U postgres -d openwebui -c "
UPDATE \"user\" SET role = 'admin' 
WHERE email = 'your-email@domain.com';
"
```

### Issue: Admin Activator Service Fails

**Check Database Connection**
```bash
# Test database connectivity
docker compose exec postgres pg_isready -U postgres -d openwebui

# If database isn't ready, restart postgres
docker compose restart postgres
```

**Check Service Logs**
```bash
# View admin activator logs
docker compose logs admin-activator

# View postgres logs
docker compose logs postgres
```

**Restart Admin Activation**
```bash
# Force restart the admin activator
docker compose rm -f admin-activator
docker compose up -d admin-activator
```

### Issue: Multiple Admin Users

**List All Admins**
```bash
# Check how many admin users exist
docker compose exec postgres psql -U postgres -d openwebui -c "
SELECT u.name, u.email, u.role, a.active 
FROM \"user\" u 
JOIN auth a ON u.id = a.id 
WHERE u.role = 'admin';
"
```

**Demote Extra Admins** (if needed)
```bash
# Change role from admin to user
docker compose exec postgres psql -U postgres -d openwebui -c "
UPDATE \"user\" SET role = 'user' 
WHERE email = 'user-to-demote@domain.com';
"
```

## 🛠️ Advanced Configuration

### Custom Admin Activation Logic

Create a custom activation script by modifying `scripts/activate_first_admin.py`:

```python
def custom_admin_activation():
    """Custom logic for admin activation."""
    
    # Example: Activate users from specific domain
    activate_users_by_domain('@company.com')
    
    # Example: Activate users by role
    activate_users_by_criteria({'department': 'IT'})
    
    # Example: Batch activate from CSV
    activate_users_from_file('admin_users.csv')
```

### Production Security

For production deployments:

1. **Disable Auto-Activation**
   ```bash
   AUTO_ACTIVATE_FIRST_ADMIN=false
   ```

2. **Manual Admin Creation**
   ```bash
   # Create admin users manually after deployment
   python3 scripts/activate_first_admin.py --email admin@company.com --role admin
   ```

3. **Regular Admin Audits**
   ```bash
   # Regularly check admin users
   python3 scripts/activate_first_admin.py --list > admin_audit.log
   ```

## 📋 Pre-Deployment Checklist

Before deploying to production:

- [ ] Set `AUTO_ACTIVATE_FIRST_ADMIN=false` in production
- [ ] Plan manual admin user creation process
- [ ] Test admin activation script in staging
- [ ] Document admin access procedures
- [ ] Set up admin user monitoring
- [ ] Configure backup admin access method

## 🔐 Security Best Practices

1. **Limit Admin Users**: Only create necessary admin accounts
2. **Regular Audits**: Monitor admin user list regularly
3. **Strong Passwords**: Enforce strong password policies
4. **2FA**: Implement two-factor authentication (if available)
5. **Access Logs**: Monitor admin user activity
6. **Principle of Least Privilege**: Use role-based access control

## 📞 Getting Help

If you continue to have admin access issues:

1. **Check the logs**: `docker compose logs admin-activator`
2. **Run diagnostics**: `python3 scripts/activate_first_admin.py --list`
3. **Manual activation**: Use the database method as a last resort
4. **Contact support**: Include logs and error messages

---

**Note**: The automatic admin activation feature is designed to solve the initial setup problem while maintaining security for production deployments.