"""
Test Runner Script
Run all tests with coverage reporting
"""
import os
import subprocess
import sys


def run_tests():
    """Run all tests with pytest"""
    print("🧪 Running test suite...")
    print("=" * 60)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    
    # Run pytest
    cmd = [
        'pytest',
        '--verbose',
        '--cov=agents',
        '--cov=authentication',
        '--cov-report=html',
        '--cov-report=term-missing',
        '--maxfail=5'
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        
        print("\n" + "=" * 60)
        if result.returncode == 0:
            print("✅ All tests passed!")
            print("📊 Coverage report generated in htmlcov/index.html")
        else:
            print("❌ Some tests failed!")
            print(f"Exit code: {result.returncode}")
        
        return result.returncode
    
    except FileNotFoundError:
        print("❌ pytest not found. Install it with: pip install pytest pytest-django pytest-cov")
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"❌ Error running tests: {e!s}")
        return 1

def run_specific_tests(test_path):
    """Run specific test file or directory"""
    print(f"🧪 Running tests: {test_path}")
    print("=" * 60)
    
    cmd = ['pytest', test_path, '--verbose']
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:  # noqa: BLE001
        print(f"❌ Error: {e!s}")
        return 1

def run_unit_tests():
    """Run only unit tests"""
    print("🧪 Running unit tests...")
    cmd = ['pytest', '-m', 'unit', '--verbose']
    subprocess.run(cmd, check=False)

def run_integration_tests():
    """Run only integration tests"""
    print("🧪 Running integration tests...")
    cmd = ['pytest', '-m', 'integration', '--verbose']
    subprocess.run(cmd, check=False)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'unit':
            run_unit_tests()
        elif sys.argv[1] == 'integration':
            run_integration_tests()
        else:
            run_specific_tests(sys.argv[1])
    else:
        exit_code = run_tests()
        sys.exit(exit_code)
