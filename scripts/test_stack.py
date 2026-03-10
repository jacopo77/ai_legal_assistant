#!/usr/bin/env python3
"""
End-to-end test script for AI Legal Assistant
Tests backend health, database connection, and chat functionality
"""

import sys
import requests
import json
from typing import Optional

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(msg: str):
    print(f"{GREEN}✓{RESET} {msg}")

def print_error(msg: str):
    print(f"{RED}✗{RESET} {msg}")

def print_info(msg: str):
    print(f"{BLUE}ℹ{RESET} {msg}")

def print_warning(msg: str):
    print(f"{YELLOW}⚠{RESET} {msg}")

def test_health_check(base_url: str) -> bool:
    """Test basic health check endpoint"""
    print_info(f"Testing health check: {base_url}/healthz")
    try:
        response = requests.get(f"{base_url}/healthz", timeout=10)
        if response.status_code == 200 and response.json().get("status") == "ok":
            print_success("Health check passed")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Health check failed: {e}")
        return False

def test_database_connection(base_url: str) -> bool:
    """Test database connectivity"""
    print_info(f"Testing database connection: {base_url}/api/health/db")
    try:
        response = requests.get(f"{base_url}/api/health/db", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok" and data.get("database") == "connected":
                print_success("Database connection passed")
                return True
        print_error(f"Database check failed: {response.status_code}")
        return False
    except requests.exceptions.RequestException as e:
        print_error(f"Database check failed: {e}")
        return False

def test_chat_stream(base_url: str, question: str = "What makes a contract valid?", country: str = "US") -> bool:
    """Test streaming chat endpoint"""
    print_info(f"Testing chat endpoint: {base_url}/api/chat/stream")
    print_info(f"Question: '{question}' (Country: {country})")
    
    try:
        response = requests.post(
            f"{base_url}/api/chat/stream",
            json={"question": question, "country": country},
            stream=True,
            timeout=30
        )
        
        if response.status_code != 200:
            print_error(f"Chat request failed: {response.status_code}")
            return False
        
        # Collect streamed response
        full_response = ""
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                full_response += chunk
        
        if full_response:
            print_success("Chat streaming successful")
            print_info(f"Response preview: {full_response[:200]}...")
            
            # Check for citations
            if "[1]" in full_response or "[2]" in full_response:
                print_success("Citations found in response")
            else:
                print_warning("No citations found (may be expected if no documents ingested)")
            
            return True
        else:
            print_error("Empty response from chat endpoint")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Chat test failed: {e}")
        return False

def test_cors(base_url: str, origin: str) -> bool:
    """Test CORS configuration"""
    print_info(f"Testing CORS with origin: {origin}")
    try:
        response = requests.options(
            f"{base_url}/api/chat/stream",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            cors_header = response.headers.get("Access-Control-Allow-Origin")
            if cors_header and (cors_header == origin or cors_header == "*"):
                print_success(f"CORS configured correctly: {cors_header}")
                return True
            else:
                print_warning(f"CORS header: {cors_header}")
                return False
        else:
            print_error(f"CORS preflight failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"CORS test failed: {e}")
        return False

def run_all_tests(base_url: str, frontend_url: Optional[str] = None):
    """Run all tests and print summary"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}AI Legal Assistant - Test Suite{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    print(f"Backend URL: {base_url}")
    if frontend_url:
        print(f"Frontend URL: {frontend_url}\n")
    
    results = {}
    
    # Run tests
    print(f"\n{BLUE}[1/4] Testing Backend Health{RESET}")
    results['health'] = test_health_check(base_url)
    
    print(f"\n{BLUE}[2/4] Testing Database Connection{RESET}")
    results['database'] = test_database_connection(base_url)
    
    print(f"\n{BLUE}[3/4] Testing Chat Functionality{RESET}")
    results['chat'] = test_chat_stream(base_url)
    
    if frontend_url:
        print(f"\n{BLUE}[4/4] Testing CORS Configuration{RESET}")
        results['cors'] = test_cors(base_url, frontend_url)
    else:
        print(f"\n{YELLOW}[4/4] Skipping CORS test (no frontend URL provided){RESET}")
        results['cors'] = None
    
    # Print summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else (f"{RED}FAIL{RESET}" if result is False else f"{YELLOW}SKIP{RESET}")
        print(f"{test_name.ljust(15)}: {status}")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"Total: {total} | Passed: {GREEN}{passed}{RESET} | Failed: {RED}{failed}{RESET} | Skipped: {YELLOW}{skipped}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    if failed == 0 and passed > 0:
        print(f"{GREEN}🎉 All tests passed! Your application is working correctly.{RESET}\n")
        return 0
    elif failed > 0:
        print(f"{RED}❌ Some tests failed. Please check the errors above.{RESET}\n")
        return 1
    else:
        print(f"{YELLOW}⚠ No tests completed successfully.{RESET}\n")
        return 1

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python test_stack.py <backend_url> [frontend_url]")
        print("\nExamples:")
        print("  python test_stack.py http://127.0.0.1:8000")
        print("  python test_stack.py https://your-app.railway.app")
        print("  python test_stack.py https://your-app.railway.app https://your-app.vercel.app")
        sys.exit(1)
    
    backend_url = sys.argv[1].rstrip('/')
    frontend_url = sys.argv[2].rstrip('/') if len(sys.argv) > 2 else None
    
    exit_code = run_all_tests(backend_url, frontend_url)
    sys.exit(exit_code)
