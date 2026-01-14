#!/usr/bin/env python
"""
Test runner script with convenient options for B2B Marketing Automation Platform

Usage:
    python tests/run_tests.py --all              # Run all tests
    python tests/run_tests.py --e2e              # Run end-to-end tests
    python tests/run_tests.py --integration      # Run integration tests
    python tests/run_tests.py --load            # Run load tests
    python tests/run_tests.py --quick           # Run quick tests only
    python tests/run_tests.py --coverage        # Run with coverage report
    python tests/run_tests.py --services        # Check services health
"""
import subprocess
import sys
import os
import argparse
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def check_services():
    """Check if all required services are running"""
    print_header("CHECKING SERVICES")

    services = {
        "PostgreSQL": {
            "type": "database",
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", 5432)),
            "database": os.getenv("POSTGRES_DB", "marketing_db"),
            "user": os.getenv("POSTGRES_USER", "marketing_user"),
            "password": os.getenv("POSTGRES_PASSWORD", "marketing_pass")
        },
        "n8n": {
            "type": "http",
            "url": os.getenv("N8N_BASE_URL", "http://localhost:5678")
        },
        "LangChain Service": {
            "type": "http",
            "url": f"{os.getenv('LANGCHAIN_SERVICE_URL', 'http://localhost:8001')}/health"
        },
        "Chroma": {
            "type": "http",
            "url": "http://localhost:8000/api/v1/heartbeat"
        },
        "Ollama": {
            "type": "http",
            "url": "http://localhost:11434"
        }
    }

    all_healthy = True

    for name, config in services.items():
        if config["type"] == "database":
            try:
                conn = psycopg2.connect(
                    host=config["host"],
                    port=config["port"],
                    database=config["database"],
                    user=config["user"],
                    password=config["password"]
                )
                conn.close()
                print_success(f"{name} is running")
            except Exception as e:
                print_error(f"{name} is not accessible: {str(e)}")
                all_healthy = False

        elif config["type"] == "http":
            try:
                response = requests.get(config["url"], timeout=5)
                if response.status_code < 500:
                    print_success(f"{name} is running")
                else:
                    print_error(f"{name} returned status {response.status_code}")
                    all_healthy = False
            except requests.exceptions.RequestException as e:
                print_error(f"{name} is not accessible: {str(e)}")
                all_healthy = False

    print()
    if all_healthy:
        print_success("All services are healthy!")
        return True
    else:
        print_error("Some services are not running. Start them with: docker-compose up -d")
        return False


def run_pytest(args_list):
    """Run pytest with given arguments"""
    cmd = ["pytest"] + args_list
    print(f"\n{Colors.BOLD}Running: {' '.join(cmd)}{Colors.RESET}\n")

    result = subprocess.run(cmd)
    return result.returncode == 0


def run_all_tests():
    """Run all tests"""
    print_header("RUNNING ALL TESTS")
    return run_pytest(["tests/", "-v"])


def run_e2e_tests():
    """Run end-to-end tests"""
    print_header("RUNNING END-TO-END TESTS")
    return run_pytest(["tests/", "-m", "e2e", "-v"])


def run_integration_tests():
    """Run integration tests"""
    print_header("RUNNING INTEGRATION TESTS")
    return run_pytest(["tests/", "-m", "integration", "-v"])


def run_quick_tests():
    """Run quick tests (exclude slow tests)"""
    print_header("RUNNING QUICK TESTS")
    return run_pytest(["tests/", "-m", "not slow", "-v"])


def run_with_coverage():
    """Run tests with coverage report"""
    print_header("RUNNING TESTS WITH COVERAGE")
    success = run_pytest([
        "tests/",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term",
        "-v"
    ])

    if success:
        print_success("\nCoverage report generated: htmlcov/index.html")

    return success


def run_load_tests():
    """Run load tests with Locust"""
    print_header("RUNNING LOAD TESTS")

    print(f"{Colors.YELLOW}Starting Locust load testing...{Colors.RESET}")
    print(f"{Colors.YELLOW}Open http://localhost:8089 in your browser{Colors.RESET}\n")

    cmd = [
        "locust",
        "-f", "tests/load_test_workflows.py",
        "--host=http://localhost:5678"
    ]

    subprocess.run(cmd)
    return True


def run_specific_test(test_path):
    """Run a specific test file or test"""
    print_header(f"RUNNING SPECIFIC TEST: {test_path}")
    return run_pytest([test_path, "-v"])


def main():
    parser = argparse.ArgumentParser(
        description="Test runner for B2B Marketing Automation Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_tests.py --all                    Run all tests
  python tests/run_tests.py --e2e                    Run end-to-end tests
  python tests/run_tests.py --integration            Run integration tests
  python tests/run_tests.py --quick                  Run quick tests only
  python tests/run_tests.py --coverage               Run with coverage report
  python tests/run_tests.py --load                   Run load tests
  python tests/run_tests.py --services               Check services health
  python tests/run_tests.py --test tests/test_e2e_content_generation.py
        """
    )

    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--quick", action="store_true", help="Run quick tests (exclude slow)")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--load", action="store_true", help="Run load tests")
    parser.add_argument("--services", action="store_true", help="Check services health")
    parser.add_argument("--test", type=str, help="Run specific test file or test")

    args = parser.parse_args()

    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    success = True

    # Check services first (except for --services flag which only checks)
    if not args.services and not args.load:
        if not check_services():
            print_warning("Some services are not running. Tests may fail.")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                sys.exit(1)

    # Run requested tests
    if args.services:
        success = check_services()

    elif args.all:
        success = run_all_tests()

    elif args.e2e:
        success = run_e2e_tests()

    elif args.integration:
        success = run_integration_tests()

    elif args.quick:
        success = run_quick_tests()

    elif args.coverage:
        success = run_with_coverage()

    elif args.load:
        success = run_load_tests()

    elif args.test:
        success = run_specific_test(args.test)

    # Print summary
    print("\n" + "=" * 60)
    if success:
        print_success("Tests completed successfully!")
    else:
        print_error("Tests failed. Check output above for details.")
    print("=" * 60 + "\n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
