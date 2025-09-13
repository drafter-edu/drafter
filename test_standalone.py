#!/usr/bin/env python3
"""
Simple standalone test to verify browser and server integration works.
This can help debug issues independently of pytest fixtures.
"""

import time
import requests
from tests.helpers import TestServer

def test_server_and_basic_connection():
    """Test that server starts and responds to HTTP requests"""
    print("Testing server startup and HTTP response...")
    
    server = TestServer()
    try:
        with server:
            print("✓ Server started successfully")
            
            # Test HTTP connection
            response = requests.get('http://localhost:8080', timeout=5)
            print(f"✓ HTTP response received: {response.status_code}")
            
            # Test content
            if 'Hello world' in response.text and 'Welcome to Drafter' in response.text:
                print("✓ Expected content found")
                return True
            else:
                print("✗ Expected content not found")
                return False
                
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_server_and_basic_connection()
    if success:
        print("\n🎉 Server test passed!")
    else:
        print("\n❌ Server test failed!")
        exit(1)