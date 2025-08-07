"""
Test script for the Simple MCP implementation
"""

import requests
import json
import time
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mcp_client import SimpleMCPClient


def test_mcp_server(server_url="http://localhost:5000"):
    """Test the MCP server endpoints."""
    
    print("🧪 Testing MCP Server...")
    
    try:
        # Test health check
        print("1. Testing health check...")
        response = requests.get(f"{server_url}/health")
        print(f"   Health: {response.json()}")
        
        # Test tools listing
        print("\n2. Testing tools listing...")
        response = requests.get(f"{server_url}/tools")
        tools = response.json()["tools"]
        print(f"   Available tools: {[tool['name'] for tool in tools]}")
        
        # Test weather tool
        print("\n3. Testing weather tool...")
        weather_data = {
            "tool_name": "get_weather",
            "parameters": {
                "location": "San Francisco, CA",
                "units": "celsius"
            }
        }
        response = requests.post(f"{server_url}/execute", json=weather_data)
        print(f"   Weather result: {json.dumps(response.json(), indent=2)}")
        
        # Test trip calculator
        print("\n4. Testing trip calculator...")
        trip_data = {
            "tool_name": "trip_calculator", 
            "parameters": {
                "from_city": "New York",
                "to_city": "Los Angeles",
                "travel_type": "flight",
                "days": 5
            }
        }
        response = requests.post(f"{server_url}/execute", json=trip_data)
        print(f"   Trip result: {json.dumps(response.json(), indent=2)}")
        
        # Test currency converter
        print("\n5. Testing currency converter...")
        currency_data = {
            "tool_name": "currency_converter",
            "parameters": {
                "amount": 1000,
                "from_currency": "USD",
                "to_currency": "EUR"
            }
        }
        response = requests.post(f"{server_url}/execute", json=currency_data)
        print(f"   Currency result: {json.dumps(response.json(), indent=2)}")
        
        print("\n✅ MCP Server tests completed successfully!")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to MCP server at {server_url}")
        print("   Make sure to start the server first with: python mcp_server.py")
        return False
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False


def test_mcp_client():
    """Test the MCP client with LLM integration."""
    
    print("\n🧪 Testing MCP Client with LLM...")
    
    try:
        client = SimpleMCPClient()
        
        print("Available tools:", [tool["name"] for tool in client.get_tools()])
        
        # Test queries
        test_queries = [
            "What's the weather in Tokyo?",
            "Calculate 25 * 8",
            "Tell me about attractions in Rome"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Testing query: '{query}'")
            response = client.chat_with_tools(query)
            print(f"   Response: {response}")
        
        print("\n✅ MCP Client tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing MCP client: {e}")
        print("   Make sure your LLM Gateway is properly configured.")
        return False


def register_mcp_server_with_gateway(gateway_url="http://localhost:8080", server_url="http://localhost:5000"):
    """Register the MCP server with the LLM Gateway (based on doc.md)."""
    
    print(f"\n🔗 Registering MCP Server with LLM Gateway...")
    
    try:
        # Create MCP server registration (from doc.md)
        mcp_data = {
            "name": "Simple Trip MCP Server",
            "url": server_url,
            "authentication_secret_key": "demo_secret_key"
        }
        
        response = requests.post(f"{gateway_url}/mcp-servers", json=mcp_data)
        
        if response.status_code == 201 or response.status_code == 200:
            result = response.json()
            server_id = result.get('id', 'unknown')
            print(f"✅ MCP Server registered successfully!")
            print(f"   Server ID: {server_id}")
            print(f"   You can now test tools at: {gateway_url}/mcp-servers/{server_id}/tools")
            return server_id
        else:
            print(f"❌ Failed to register MCP server: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to LLM Gateway at {gateway_url}")
        print("   Make sure the LLM Gateway is running.")
        return None
    except Exception as e:
        print(f"❌ Error registering MCP server: {e}")
        return None


def main():
    """Run all MCP tests."""
    
    print("🚀 Simple MCP Implementation Test Suite")
    print("=" * 50)
    
    # Test 1: Test MCP Server directly
    server_success = test_mcp_server()
    
    # Test 2: Test MCP Client with LLM
    client_success = test_mcp_client()
    
    # Test 3: Register with LLM Gateway (optional)
    print("\n" + "=" * 50)
    print("Optional: Register MCP Server with LLM Gateway")
    register_choice = input("Do you want to register the MCP server with the LLM Gateway? (y/n): ").lower()
    
    if register_choice == 'y':
        gateway_url = input("Enter LLM Gateway URL (default: http://localhost:8080): ").strip()
        if not gateway_url:
            gateway_url = "http://localhost:8080"
        
        server_id = register_mcp_server_with_gateway(gateway_url)
        
        if server_id:
            print(f"\n🎉 You can now test the registered tools using curl:")
            print(f"curl -X GET {gateway_url}/mcp-servers/{server_id}/tools")
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   MCP Server: {'✅ PASS' if server_success else '❌ FAIL'}")
    print(f"   MCP Client: {'✅ PASS' if client_success else '❌ FAIL'}")
    
    if server_success and client_success:
        print("\n🎉 All tests passed! Your MCP implementation is working.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    main()