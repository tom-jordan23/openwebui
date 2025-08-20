#!/usr/bin/env python3
"""
Prompt Management System Validation Script
Validates the complete prompt management system functionality
"""

import sys
import json
import time
import requests
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.prompt_management import PromptService, PromptTemplateProcessor, PromptExportImport
from src.database.connection import get_db_connection

class PromptSystemValidator:
    """Validates the complete prompt management system"""
    
    def __init__(self):
        self.service = PromptService()
        self.results = {
            'database_layer': False,
            'api_layer': False,
            'template_processing': False,
            'import_export': False,
            'error_handling': False,
            'performance': False
        }
        self.errors = []
    
    def validate_database_layer(self):
        """Validate database layer functionality"""
        print("🔍 Validating Database Layer...")
        
        try:
            # Test database connection
            db = get_db_connection()
            if not db.test_connection():
                raise Exception("Database connection failed")
            
            # Test database schema exists
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('prompt_version', 'prompt_category')
                """)
                tables = [row['table_name'] for row in cursor.fetchall()]
                
                if 'prompt_version' not in tables:
                    raise Exception("prompt_version table not found")
                if 'prompt_category' not in tables:
                    raise Exception("prompt_category table not found")
                    
            # Create validator user if it doesn't exist
            with db.get_transaction() as cursor:
                current_time = int(time.time() * 1000)
                cursor.execute("""
                    INSERT INTO "user" (id, name, email, role, profile_image_url, created_at, updated_at, last_active_at, api_key, settings, info)
                    VALUES ('validator', 'Validator User', 'validator@test.com', 'user', '', %s, %s, %s, %s, '{}', '{}')
                    ON CONFLICT (id) DO NOTHING
                """, (current_time, current_time, current_time, f'validator-api-{current_time}'))
            
            self.results['database_layer'] = True
            print("✅ Database layer validation passed")
            
        except Exception as e:
            self.errors.append(f"Database layer: {e}")
            print(f"❌ Database layer validation failed: {e}")
    
    def validate_api_layer(self):
        """Validate API layer functionality"""
        print("🔍 Validating API Layer...")
        
        try:
            # Test category operations
            category_data = {
                'name': f'Test Category {int(time.time())}',
                'description': 'A test category for validation',
                'created_by': 'validator'
            }
            
            # Create category
            result = self.service.create_category(category_data)
            if not result['success']:
                raise Exception(f"Category creation failed: {result.get('error', 'Unknown error')}")
            
            # Get categories
            categories_result = self.service.get_categories()
            if not categories_result['success']:
                raise Exception(f"Get categories failed: {categories_result.get('error', 'Unknown error')}")
            
            self.results['api_layer'] = True
            print("✅ API layer validation passed")
            
        except Exception as e:
            self.errors.append(f"API layer: {e}")
            print(f"❌ API layer validation failed: {e}")
    
    def validate_template_processing(self):
        """Validate template processing functionality"""
        print("🔍 Validating Template Processing...")
        
        try:
            # Test template with various variable types
            template_content = """
            Hello {name},
            
            You are working on {project_type} with {team_size} people.
            Your deadline is {deadline} and the priority is {priority}.
            
            Additional notes: {notes}
            """
            
            # Test variable extraction
            variables = PromptTemplateProcessor.extract_variables(template_content)
            expected_vars = {'name', 'project_type', 'team_size', 'deadline', 'priority', 'notes'}
            if set(variables) != expected_vars:
                raise Exception(f"Variable extraction failed. Expected {expected_vars}, got {set(variables)}")
            
            # Test variable validation
            test_vars = {
                'name': 'John Doe',
                'project_type': 'Web Application',
                'team_size': '5',
                'deadline': '2025-01-15',
                'priority': 'High',
                'notes': 'Focus on performance optimization'
            }
            
            validation = PromptTemplateProcessor.validate_variables(template_content, test_vars)
            if not validation['valid']:
                raise Exception(f"Variable validation failed: {validation}")
            
            # Test template processing
            processed = PromptTemplateProcessor.process_template(template_content, test_vars)
            
            # Verify all variables were replaced
            for var_name in variables:
                if f'{{{var_name}}}' in processed:
                    raise Exception(f"Variable {var_name} was not replaced in template")
                if test_vars[var_name] not in processed:
                    raise Exception(f"Variable value {test_vars[var_name]} not found in processed template")
            
            # Test edge cases
            empty_template = ""
            empty_vars = PromptTemplateProcessor.extract_variables(empty_template)
            if len(empty_vars) != 0:
                raise Exception("Empty template should return no variables")
            
            # Test malformed variables
            malformed_template = "Hello {name} and {incomplete"
            malformed_vars = PromptTemplateProcessor.extract_variables(malformed_template)
            if 'incomplete' in malformed_vars:
                raise Exception("Should not extract incomplete variable")
            
            self.results['template_processing'] = True
            print("✅ Template processing validation passed")
            
        except Exception as e:
            self.errors.append(f"Template processing: {e}")
            print(f"❌ Template processing validation failed: {e}")
    
    def validate_import_export(self):
        """Validate import/export functionality"""
        print("🔍 Validating Import/Export...")
        
        try:
            # Create test data structure
            test_export_data = {
                'prompt': {
                    'id': 1,
                    'title': 'Test Export Prompt',
                    'content': 'Test export content'
                },
                'versions': [
                    {
                        'id': 1,
                        'prompt_id': 1,
                        'version_number': 1,
                        'title': 'Export Test Version',
                        'content': 'Hello {user}, this is a test of {feature}!',
                        'variables': {'user': 'string', 'feature': 'string'},
                        'created_by': 'validator'
                    }
                ],
                'export_timestamp': int(time.time() * 1000),
                'export_version': '1.0'
            }
            
            # Test JSON serialization/deserialization
            json_data = json.dumps(test_export_data)
            parsed_data = json.loads(json_data)
            
            # Verify data integrity
            if parsed_data['prompt']['title'] != test_export_data['prompt']['title']:
                raise Exception("JSON serialization failed - data corruption")
            
            if len(parsed_data['versions']) != 1:
                raise Exception("Version data not properly serialized")
            
            # Test template variables in exported content
            version_content = parsed_data['versions'][0]['content']
            extracted_vars = PromptTemplateProcessor.extract_variables(version_content)
            if set(extracted_vars) != {'user', 'feature'}:
                raise Exception("Template variables not preserved in export")
            
            self.results['import_export'] = True
            print("✅ Import/Export validation passed")
            
        except Exception as e:
            self.errors.append(f"Import/Export: {e}")
            print(f"❌ Import/Export validation failed: {e}")
    
    def validate_error_handling(self):
        """Validate error handling across the system"""
        print("🔍 Validating Error Handling...")
        
        try:
            # Test missing required fields
            invalid_category = {'description': 'Missing name field'}
            result = self.service.create_category(invalid_category)
            if result['success']:
                raise Exception("Should have failed with missing required field")
            if 'Missing required field' not in result['error']:
                raise Exception("Error message should mention missing required field")
            
            # Test template processing with missing variables
            template = "Hello {name}, welcome to {system}!"
            incomplete_vars = {'name': 'John'}  # Missing 'system'
            
            validation = PromptTemplateProcessor.validate_variables(template, incomplete_vars)
            if validation['valid']:
                raise Exception("Should have failed validation with missing variables")
            if 'system' not in validation['missing_variables']:
                raise Exception("Should have identified 'system' as missing variable")
            
            # Test processing with missing variables (should not crash)
            try:
                processed = PromptTemplateProcessor.process_template(template, incomplete_vars)
                # Should replace available variables, leave missing ones
                if 'John' not in processed:
                    raise Exception("Should have replaced available variables")
                if '{system}' not in processed:
                    raise Exception("Should have left missing variables as placeholders")
            except Exception as e:
                raise Exception(f"Template processing should not crash with missing variables: {e}")
            
            self.results['error_handling'] = True
            print("✅ Error handling validation passed")
            
        except Exception as e:
            self.errors.append(f"Error handling: {e}")
            print(f"❌ Error handling validation failed: {e}")
    
    def validate_performance(self):
        """Validate system performance"""
        print("🔍 Validating Performance...")
        
        try:
            # Test template processing performance
            large_template = """
            Project: {project_name}
            Description: {description}
            Team: {team_members}
            Timeline: {start_date} to {end_date}
            Budget: {budget}
            Requirements: {requirements}
            Constraints: {constraints}
            Success Criteria: {success_criteria}
            Risks: {risks}
            Mitigation: {mitigation_strategies}
            """ * 10  # Repeat to make it larger
            
            test_vars = {
                'project_name': 'Large Scale Application',
                'description': 'A comprehensive web application with multiple modules',
                'team_members': 'Alice, Bob, Carol, David, Eve',
                'start_date': '2025-01-01',
                'end_date': '2025-12-31',
                'budget': '$500,000',
                'requirements': 'High performance, scalability, security, user-friendly interface',
                'constraints': 'Limited budget, tight timeline, regulatory compliance',
                'success_criteria': '99.9% uptime, <2s response time, 10k concurrent users',
                'risks': 'Technical complexity, changing requirements, resource availability',
                'mitigation_strategies': 'Regular reviews, agile methodology, risk assessment'
            }
            
            # Measure processing time
            start_time = time.time()
            for _ in range(100):  # Process 100 times
                processed = PromptTemplateProcessor.process_template(large_template, test_vars)
            end_time = time.time()
            
            processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
            avg_time_per_process = processing_time / 100
            
            # Should process large templates quickly (under 10ms per template)
            if avg_time_per_process > 10:
                raise Exception(f"Template processing too slow: {avg_time_per_process:.2f}ms per template")
            
            # Test variable extraction performance
            start_time = time.time()
            for _ in range(1000):  # Extract variables 1000 times
                variables = PromptTemplateProcessor.extract_variables(large_template)
            end_time = time.time()
            
            extraction_time = (end_time - start_time) * 1000
            avg_extraction_time = extraction_time / 1000
            
            # Should extract variables quickly (under 1ms per extraction)
            if avg_extraction_time > 1:
                raise Exception(f"Variable extraction too slow: {avg_extraction_time:.2f}ms per extraction")
            
            self.results['performance'] = True
            print(f"✅ Performance validation passed (avg processing: {avg_time_per_process:.2f}ms, avg extraction: {avg_extraction_time:.2f}ms)")
            
        except Exception as e:
            self.errors.append(f"Performance: {e}")
            print(f"❌ Performance validation failed: {e}")
    
    def run_validation(self):
        """Run complete system validation"""
        print("🚀 Starting Prompt Management System Validation")
        print("=" * 60)
        
        # Run all validations
        self.validate_database_layer()
        self.validate_api_layer()
        self.validate_template_processing()
        self.validate_import_export()
        self.validate_error_handling()
        self.validate_performance()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Validation Summary")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        
        for component, passed in self.results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{component.replace('_', ' ').title():<25} {status}")
        
        print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
        
        if self.errors:
            print(f"\n❌ Errors encountered:")
            for error in self.errors:
                print(f"  • {error}")
        
        if passed_tests == total_tests:
            print("\n🎉 All validations passed! The prompt management system is ready for use.")
            return True
        else:
            print(f"\n⚠️  {total_tests - passed_tests} validation(s) failed. Please review and fix the issues.")
            return False

def main():
    """Main validation function"""
    validator = PromptSystemValidator()
    success = validator.run_validation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()