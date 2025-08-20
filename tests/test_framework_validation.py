"""
Testing framework validation for Phase 1.3 completion
"""
import pytest
import os
import subprocess


class TestFrameworkValidation:
    """Validate the testing framework is properly set up"""

    def test_virtual_environment_exists(self):
        """Test that virtual environment is set up correctly"""
        assert os.path.exists("venv/bin/pytest"), "Virtual environment not set up properly"
        assert os.path.exists("venv/bin/pip"), "Pip not available in virtual environment"

    def test_pytest_configuration(self):
        """Test that pytest is configured correctly"""
        assert os.path.exists("pytest.ini"), "pytest.ini configuration file missing"
        
        with open("pytest.ini", "r") as f:
            content = f.read()
            assert "testpaths = tests" in content
            assert "--cov-fail-under=80" in content

    def test_test_requirements_installed(self):
        """Test that all required testing packages are installed"""
        result = subprocess.run(
            ["./venv/bin/pip", "list"], 
            capture_output=True, 
            text=True
        )
        
        required_packages = [
            "pytest",
            "pytest-cov", 
            "requests",
            "psycopg2-binary",
            "redis"
        ]
        
        for package in required_packages:
            assert package in result.stdout, f"Required package {package} not installed"

    def test_test_directories_exist(self):
        """Test that test directory structure exists"""
        assert os.path.exists("tests/"), "Tests directory missing"
        assert os.path.exists("tests/unit/"), "Unit tests directory missing"
        assert os.path.exists("tests/integration/"), "Integration tests directory missing"
        assert os.path.exists("tests/conftest.py"), "Test configuration missing"

    def test_makefile_commands_exist(self):
        """Test that Makefile includes testing commands"""
        with open("Makefile", "r") as f:
            content = f.read()
            
        required_commands = [
            "test-setup:",
            "test-unit:",
            "test-integration-pytest:",
            "test-coverage:",
            "test-all:"
        ]
        
        for command in required_commands:
            assert command in content, f"Makefile missing {command} target"

    def test_basic_service_connectivity(self, docker_services):
        """Test that all required services are accessible for testing"""
        # This test uses the docker_services fixture to ensure services are running
        # The fixture handles the actual connectivity testing
        assert True  # If we get here, docker_services fixture passed


class TestCoverageRequirements:
    """Test that coverage requirements are met"""

    def test_unit_test_coverage_requirement(self):
        """Test that unit tests meet the 80% coverage requirement"""
        # Run coverage analysis on unit tests
        result = subprocess.run([
            "./venv/bin/pytest", 
            "tests/unit/", 
            "--cov=tests/unit", 
            "--cov-report=term-missing",
            "--cov-fail-under=80",
            "-q"
        ], capture_output=True, text=True)
        
        # Should not fail due to coverage
        assert result.returncode == 0, f"Unit tests failed coverage requirement: {result.stdout}"
        
        # Check that coverage is reported
        assert "TOTAL" in result.stdout, "Coverage report not generated"

    def test_test_framework_completeness(self):
        """Test that the testing framework meets Phase 1.3 requirements"""
        # Check that we have:
        # 1. Unit tests for service health
        # 2. Integration tests for service interactions  
        # 3. Configuration for CI/CD pipeline
        # 4. Coverage reporting setup
        # 5. Test database and mock services capability
        
        assertions = [
            ("Unit tests exist", os.path.exists("tests/unit/test_services.py")),
            ("Integration tests exist", os.path.exists("tests/integration/test_service_integration.py")),
            ("Test configuration exists", os.path.exists("tests/conftest.py")),
            ("Coverage configuration exists", os.path.exists("pytest.ini")),
            ("Virtual environment ready", os.path.exists("venv/bin/pytest")),
        ]
        
        for description, assertion in assertions:
            assert assertion, f"Framework requirement not met: {description}"