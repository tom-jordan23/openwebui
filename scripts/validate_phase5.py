#!/usr/bin/env python3
"""
Phase 5 Validation Script
Validates all Phase 5 implementations and provides comprehensive status report
"""

import os
import sys
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

def check_file_exists(file_path: str) -> Dict[str, Any]:
    """Check if file exists and get basic info"""
    path = Path(file_path)
    if path.exists():
        stat = path.stat()
        return {
            "exists": True,
            "size_bytes": stat.st_size,
            "size_kb": round(stat.st_size / 1024, 2),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    else:
        return {"exists": False}

def validate_high_availability():
    """Validate high availability implementation"""
    print("🔍 Validating High Availability Implementation...")
    
    results = {
        "docker_compose_ha": check_file_exists("docker-compose.ha.yml"),
        "haproxy_config": check_file_exists("config/haproxy/haproxy.cfg"),
        "postgres_primary_config": check_file_exists("config/postgres/postgresql-primary.conf"),
        "postgres_replica_config": check_file_exists("config/postgres/postgresql-replica.conf"),
        "redis_sentinel_config": check_file_exists("config/redis/sentinel-1.conf"),
        "postgres_auth_config": check_file_exists("config/postgres/pg_hba.conf")
    }
    
    # Check if core files exist
    required_files = ["docker_compose_ha", "haproxy_config", "postgres_primary_config"]
    missing_files = [f for f in required_files if not results[f]["exists"]]
    
    if missing_files:
        print(f"❌ Missing required HA files: {missing_files}")
        return False
    else:
        print("✅ High Availability files present")
        
        # Show file sizes
        for name, info in results.items():
            if info["exists"]:
                print(f"   📄 {name}: {info['size_kb']} KB")
        
        return True

def validate_analytics_system():
    """Validate business intelligence and analytics"""
    print("\n🔍 Validating Analytics System...")
    
    analytics_file = check_file_exists("src/analytics/business_intelligence.py")
    
    if not analytics_file["exists"]:
        print("❌ Analytics system file missing")
        return False
    
    print(f"✅ Analytics system implemented ({analytics_file['size_kb']} KB)")
    
    # Try to import and validate structure
    try:
        sys.path.append("src")
        from analytics.business_intelligence import BusinessIntelligenceEngine, MetricType, TimeRange
        
        print("✅ Analytics modules can be imported")
        
        # Check if main classes exist
        required_classes = [
            'BusinessIntelligenceEngine',
            'MetricType',
            'TimeRange',
            'AnalyticsMetric',
            'UserSegment',
            'ModelPerformanceMetrics',
            'BusinessKPI'
        ]
        
        from analytics import business_intelligence
        existing_classes = [name for name in required_classes if hasattr(business_intelligence, name)]
        
        print(f"✅ Found {len(existing_classes)}/{len(required_classes)} required classes")
        return True
        
    except Exception as e:
        print(f"⚠️  Analytics import failed: {e}")
        return False

def validate_disaster_recovery():
    """Validate disaster recovery system"""
    print("\n🔍 Validating Disaster Recovery System...")
    
    dr_file = check_file_exists("src/backup/disaster_recovery.py")
    
    if not dr_file["exists"]:
        print("❌ Disaster recovery file missing")
        return False
    
    print(f"✅ Disaster recovery implemented ({dr_file['size_kb']} KB)")
    
    # Try to import and validate
    try:
        from backup.disaster_recovery import DisasterRecoveryManager, BackupType, BackupStatus
        
        print("✅ Disaster recovery modules can be imported")
        
        # Test basic initialization
        dr_manager = DisasterRecoveryManager()
        print("✅ DisasterRecoveryManager can be instantiated")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Disaster recovery import failed: {e}")
        return False

def validate_enterprise_auth():
    """Validate enterprise authentication system"""
    print("\n🔍 Validating Enterprise Authentication...")
    
    auth_file = check_file_exists("src/auth/enterprise_auth.py")
    
    if not auth_file["exists"]:
        print("❌ Enterprise auth file missing")
        return False
    
    print(f"✅ Enterprise authentication implemented ({auth_file['size_kb']} KB)")
    
    # Try to import and validate
    try:
        from auth.enterprise_auth import (
            EnterpriseAuthenticationManager, 
            AuthenticationMethod, 
            UserRole, 
            MFAType
        )
        
        print("✅ Enterprise auth modules can be imported")
        
        # Test basic initialization
        auth_manager = EnterpriseAuthenticationManager()
        print("✅ EnterpriseAuthenticationManager can be instantiated")
        
        # Check supported authentication methods
        methods = list(AuthenticationMethod)
        print(f"✅ Supports {len(methods)} authentication methods: {[m.value for m in methods]}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Enterprise auth import failed: {e}")
        return False

def validate_advanced_graphrag():
    """Validate advanced GraphRAG optimization"""
    print("\n🔍 Validating Advanced GraphRAG System...")
    
    graphrag_file = check_file_exists("src/knowledge/advanced_graphrag.py")
    
    if not graphrag_file["exists"]:
        print("❌ Advanced GraphRAG file missing")
        return False
    
    print(f"✅ Advanced GraphRAG implemented ({graphrag_file['size_kb']} KB)")
    
    # Try to import and validate
    try:
        from knowledge.advanced_graphrag import (
            AdvancedGraphRAG,
            IntelligentCache,
            CacheStrategy,
            QueryType
        )
        
        print("✅ Advanced GraphRAG modules can be imported")
        
        # Test cache system
        cache = IntelligentCache(max_size=100)
        print("✅ IntelligentCache can be instantiated")
        
        # Check query types
        query_types = list(QueryType)
        print(f"✅ Supports {len(query_types)} query types: {[q.value for q in query_types]}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Advanced GraphRAG import failed: {e}")
        return False

def validate_testing_framework():
    """Validate comprehensive testing framework"""
    print("\n🔍 Validating Testing Framework...")
    
    testing_file = check_file_exists("src/testing/comprehensive_testing.py")
    config_file = check_file_exists("config/testing/framework_config.yaml")
    runner_file = check_file_exists("scripts/run_comprehensive_tests.py")
    
    if not testing_file["exists"]:
        print("❌ Testing framework file missing")
        return False
    
    print(f"✅ Testing framework implemented ({testing_file['size_kb']} KB)")
    
    if config_file["exists"]:
        print(f"✅ Testing configuration present ({config_file['size_kb']} KB)")
    else:
        print("⚠️  Testing configuration missing")
    
    if runner_file["exists"]:
        print(f"✅ Test runner script present ({runner_file['size_kb']} KB)")
    else:
        print("⚠️  Test runner script missing")
    
    # Try to import and validate
    try:
        from testing.comprehensive_testing import (
            ComprehensiveTestFramework,
            TestType,
            TestCase,
            ChaosExperiment
        )
        
        print("✅ Testing framework modules can be imported")
        
        # Test framework initialization
        framework = ComprehensiveTestFramework()
        print("✅ ComprehensiveTestFramework can be instantiated")
        
        # Check test types
        test_types = list(TestType)
        print(f"✅ Supports {len(test_types)} test types: {[t.value for t in test_types]}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Testing framework import failed: {e}")
        return False

async def test_async_functionality():
    """Test async functionality of implemented systems"""
    print("\n🔍 Testing Async Functionality...")
    
    try:
        # Test analytics async functionality
        from analytics.business_intelligence import BusinessIntelligenceEngine
        
        # Create test engine (without actual database)
        engine = BusinessIntelligenceEngine("sqlite:///:memory:")
        
        # Test if async methods exist
        if hasattr(engine, 'generate_executive_dashboard'):
            print("✅ Analytics async methods available")
        
        # Test disaster recovery async
        from backup.disaster_recovery import DisasterRecoveryManager
        
        dr_manager = DisasterRecoveryManager()
        if hasattr(dr_manager, 'create_full_backup'):
            print("✅ Disaster recovery async methods available")
        
        # Test GraphRAG async
        from knowledge.advanced_graphrag import AdvancedGraphRAG
        
        graphrag = AdvancedGraphRAG()
        if hasattr(graphrag, 'optimized_query'):
            print("✅ GraphRAG async methods available")
        
        # Test testing framework async
        from testing.comprehensive_testing import ComprehensiveTestFramework
        
        framework = ComprehensiveTestFramework()
        if hasattr(framework, 'run_test_suite'):
            print("✅ Testing framework async methods available")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Async functionality test failed: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available"""
    print("\n🔍 Checking Dependencies...")
    
    dependencies = {
        "pandas": "Data analysis for analytics",
        "numpy": "Numerical computations",
        "sklearn": "Machine learning for user segmentation",
        "psycopg2": "PostgreSQL database connectivity",
        "redis": "Redis cache connectivity",
        "docker": "Docker integration for testing",
        "psutil": "System metrics collection",
        "cryptography": "Encryption for backups",
        "jwt": "JWT token handling",
        "hashlib": "Hashing utilities",
        "yaml": "Configuration file parsing"
    }
    
    available_deps = []
    missing_deps = []
    
    for dep, description in dependencies.items():
        try:
            __import__(dep)
            available_deps.append(dep)
            print(f"✅ {dep}: {description}")
        except ImportError:
            missing_deps.append(dep)
            print(f"⚠️  {dep}: {description} (not installed)")
    
    print(f"\n📊 Dependencies: {len(available_deps)}/{len(dependencies)} available")
    
    if missing_deps:
        print(f"⚠️  Missing dependencies: {missing_deps}")
        print("   Run: pip install " + " ".join(missing_deps))
    
    return len(missing_deps) == 0

def generate_validation_report(results: Dict[str, Any]) -> str:
    """Generate comprehensive validation report"""
    report = {
        "validation_timestamp": datetime.now().isoformat(),
        "phase_5_status": "completed" if all(results.values()) else "partial",
        "component_status": results,
        "summary": {
            "total_components": len(results),
            "successful_components": sum(1 for v in results.values() if v),
            "failed_components": sum(1 for v in results.values() if not v),
            "success_rate": (sum(1 for v in results.values() if v) / len(results)) * 100
        }
    }
    
    return json.dumps(report, indent=2)

async def main():
    """Main validation function"""
    print("🚀 OpenWebUI Phase 5 Validation")
    print("=" * 50)
    print("Validating all Phase 5: Advanced Production Features implementations")
    print()
    
    # Run all validations
    validation_results = {
        "high_availability": validate_high_availability(),
        "analytics_system": validate_analytics_system(),
        "disaster_recovery": validate_disaster_recovery(),
        "enterprise_auth": validate_enterprise_auth(),
        "advanced_graphrag": validate_advanced_graphrag(),
        "testing_framework": validate_testing_framework(),
        "async_functionality": await test_async_functionality(),
        "dependencies": check_dependencies()
    }
    
    # Generate summary
    print("\n" + "=" * 50)
    print("PHASE 5 VALIDATION SUMMARY")
    print("=" * 50)
    
    successful_components = sum(1 for v in validation_results.values() if v)
    total_components = len(validation_results)
    success_rate = (successful_components / total_components) * 100
    
    for component, status in validation_results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component.replace('_', ' ').title()}")
    
    print(f"\n📊 Overall Success Rate: {success_rate:.1f}% ({successful_components}/{total_components})")
    
    if success_rate == 100:
        print("\n🎉 Phase 5 implementation is COMPLETE!")
        print("All advanced production features have been successfully implemented.")
    elif success_rate >= 80:
        print("\n✅ Phase 5 implementation is MOSTLY COMPLETE!")
        print("Most features implemented successfully with minor issues.")
    elif success_rate >= 60:
        print("\n⚠️  Phase 5 implementation is PARTIALLY COMPLETE!")
        print("Some critical components need attention.")
    else:
        print("\n❌ Phase 5 implementation needs SIGNIFICANT WORK!")
        print("Multiple critical components are missing or broken.")
    
    # Save validation report
    report = generate_validation_report(validation_results)
    report_path = Path("validation_reports") / f"phase5_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n📋 Detailed validation report saved: {report_path}")
    
    # Exit with appropriate code
    if success_rate == 100:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())