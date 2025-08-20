#!/bin/bash
# Database migration script for AI Assistant Platform
# Applies all pending migrations in order

set -e

# Configuration
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="openwebui"
DB_USER="postgres"
DB_PASSWORD="postgres"
MIGRATIONS_DIR="$(dirname "$0")/migrations"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if database is accessible
check_database() {
    log_info "Checking database connection..."
    if docker compose exec postgres psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        log_info "Database connection successful"
    else
        log_error "Cannot connect to database. Please ensure Docker containers are running."
        exit 1
    fi
}

# Create migration tracking table
create_migration_table() {
    log_info "Creating migration tracking table..."
    docker compose exec postgres psql -U "$DB_USER" -d "$DB_NAME" -c "
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            checksum VARCHAR(255)
        );
    " > /dev/null 2>&1
}

# Get applied migrations
get_applied_migrations() {
    docker compose exec postgres psql -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT version FROM schema_migrations ORDER BY version;
    " 2>/dev/null | sed 's/^[ \t]*//;s/[ \t]*$//' | grep -v '^$' || true
}

# Calculate file checksum
calculate_checksum() {
    local file="$1"
    sha256sum "$file" | awk '{print $1}'
}

# Apply single migration
apply_migration() {
    local migration_file="$1"
    local migration_name=$(basename "$migration_file" .sql)
    local checksum=$(calculate_checksum "$migration_file")
    
    log_info "Applying migration: $migration_name"
    
    # Apply the migration
    if docker compose exec postgres psql -U "$DB_USER" -d "$DB_NAME" -f "/migrations/$(basename "$migration_file")" > /dev/null 2>&1; then
        # Record the migration
        docker compose exec postgres psql -U "$DB_USER" -d "$DB_NAME" -c "
            INSERT INTO schema_migrations (version, checksum) 
            VALUES ('$migration_name', '$checksum');
        " > /dev/null 2>&1
        log_info "✓ Migration $migration_name applied successfully"
    else
        log_error "✗ Migration $migration_name failed"
        return 1
    fi
}

# Main migration function
run_migrations() {
    log_info "Starting database migrations..."
    
    # Get list of applied migrations
    applied_migrations=$(get_applied_migrations)
    
    # Find and apply pending migrations
    migration_count=0
    for migration_file in "$MIGRATIONS_DIR"/*.sql; do
        if [[ -f "$migration_file" ]]; then
            migration_name=$(basename "$migration_file" .sql)
            
            if echo "$applied_migrations" | grep -q "^$migration_name$"; then
                log_info "Skipping already applied migration: $migration_name"
            else
                apply_migration "$migration_file"
                migration_count=$((migration_count + 1))
            fi
        fi
    done
    
    if [[ $migration_count -eq 0 ]]; then
        log_info "No pending migrations found. Database is up to date."
    else
        log_info "Applied $migration_count migration(s) successfully."
    fi
}

# Show migration status
show_status() {
    log_info "Migration Status:"
    echo "=================="
    
    # Show applied migrations
    applied_migrations=$(get_applied_migrations)
    if [[ -n "$applied_migrations" ]]; then
        echo "Applied migrations:"
        echo "$applied_migrations" | while read -r migration; do
            if [[ -n "$migration" ]]; then
                echo "  ✓ $migration"
            fi
        done
    else
        echo "  No migrations applied yet"
    fi
    
    echo ""
    
    # Show pending migrations
    pending_count=0
    echo "Pending migrations:"
    for migration_file in "$MIGRATIONS_DIR"/*.sql; do
        if [[ -f "$migration_file" ]]; then
            migration_name=$(basename "$migration_file" .sql)
            
            if ! echo "$applied_migrations" | grep -q "^$migration_name$"; then
                echo "  - $migration_name"
                pending_count=$((pending_count + 1))
            fi
        fi
    done
    
    if [[ $pending_count -eq 0 ]]; then
        echo "  No pending migrations"
    fi
}

# Main script
main() {
    case "${1:-migrate}" in
        "migrate")
            check_database
            create_migration_table
            run_migrations
            ;;
        "status")
            check_database
            create_migration_table
            show_status
            ;;
        "help")
            echo "Usage: $0 [command]"
            echo "Commands:"
            echo "  migrate    Apply pending migrations (default)"
            echo "  status     Show migration status"
            echo "  help       Show this help"
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

main "$@"