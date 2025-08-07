"""
Test script for the Advanced MCP implementation with database
"""

import requests
import json
import time
import sys
import os
from database import WeatherDatabase

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def test_database_setup():
    """Test the database setup and basic queries."""
    print("🗄️  Testing Database Setup...")
    
    try:
        db = WeatherDatabase()
        
        # Test basic queries
        print("\n1. Testing cities table:")
        cities = db.execute_query("SELECT name, country, population FROM cities ORDER BY population DESC LIMIT 5")
        for city in cities:
            print(f"   • {city['name']}, {city['country']} - {city['population']:,} people")
        
        print("\n2. Testing weather data:")
        weather = db.execute_query("""
            SELECT c.name, w.date, w.temperature_celsius, w.condition 
            FROM cities c JOIN weather_data w ON c.id = w.city_id 
            WHERE c.name = 'Tokyo' 
            ORDER BY w.date DESC LIMIT 3
        """)
        for w in weather:
            print(f"   • {w['name']} on {w['date']}: {w['temperature_celsius']}°C, {w['condition']}")
        
        print("\n3. Testing travel destinations:")
        attractions = db.execute_query("""
            SELECT c.name, td.attraction_name, td.rating 
            FROM cities c JOIN travel_destinations td ON c.id = td.city_id 
            WHERE td.rating >= 4.5
            ORDER BY td.rating DESC LIMIT 3
        """)
        for attr in attractions:
            print(f"   • {attr['attraction_name']} in {attr['name']} - {attr['rating']}★")
        
        print("✅ Database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_advanced_mcp_server(server_url="http://localhost:5001"):
    """Test the advanced MCP server endpoints."""
    
    print(f"\n🧪 Testing Advanced MCP Server at {server_url}...")
    
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
        
        # Test database schema
        print("\n3. Testing database schema tool...")
        schema_data = {
            "tool_name": "get_database_schema",
            "parameters": {}
        }
        response = requests.post(f"{server_url}/execute", json=schema_data)
        schema_result = response.json()["result"]
        print(f"   Tables: {list(schema_result['all_tables'].keys())}")
        
        # Test SQL query tool
        print("\n4. Testing SQL query tool...")
        sql_data = {
            "tool_name": "query_weather_database",
            "parameters": {
                "sql_query": "SELECT name, country, population FROM cities ORDER BY population DESC LIMIT 3",
                "explanation": "Get the 3 most populous cities"
            }
        }
        response = requests.post(f"{server_url}/execute", json=sql_data)
        sql_result = response.json()["result"]
        print(f"   Query result: Found {sql_result['row_count']} rows")
        for row in sql_result['results']:
            print(f"     • {row['name']}, {row['country']} - {row['population']:,}")
        
        # Test weather summary tool
        print("\n5. Testing weather summary tool...")
        weather_data = {
            "tool_name": "get_weather_summary",
            "parameters": {
                "city_name": "Tokyo",
                "days": 7
            }
        }
        response = requests.post(f"{server_url}/execute", json=weather_data)
        weather_result = response.json()["result"]
        if "summary" in weather_result:
            print(f"   Tokyo weather summary: {weather_result['summary']['avg_temperature']}")
        
        # Test SQL suggestions
        print("\n6. Testing SQL suggestions...")
        suggest_data = {
            "tool_name": "suggest_sql_query",
            "parameters": {
                "description": "show me weather data for rainy days"
            }
        }
        response = requests.post(f"{server_url}/execute", json=suggest_data)
        suggest_result = response.json()["result"]
        print(f"   Generated {len(suggest_result['suggestions'])} suggestions")
        
        print("\n✅ Advanced MCP Server tests passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to MCP server at {server_url}")
        print("   Start it with: python advanced_mcp_server.py")
        return False
    except Exception as e:
        print(f"❌ Error testing advanced MCP server: {e}")
        return False


def test_complex_queries(server_url="http://localhost:5001"):
    """Test complex SQL queries that demonstrate the capabilities."""
    
    print(f"\n🔍 Testing Complex Query Scenarios...")
    
    complex_queries = [
        {
            "name": "Cities with recent precipitation",
            "query": """
                SELECT DISTINCT c.name, c.country, AVG(w.precipitation_mm) as avg_rain
                FROM cities c 
                JOIN weather_data w ON c.id = w.city_id 
                WHERE w.precipitation_mm > 0 
                AND w.date >= date('now', '-7 days')
                GROUP BY c.id, c.name, c.country
                ORDER BY avg_rain DESC
                LIMIT 5
            """,
            "explanation": "Find cities with the most rain in the past week"
        },
        {
            "name": "Temperature comparison",
            "query": """
                SELECT 
                    c.name,
                    c.country,
                    ROUND(AVG(w.temperature_celsius), 1) as avg_temp,
                    ROUND(MAX(w.temperature_celsius), 1) as max_temp,
                    ROUND(MIN(w.temperature_celsius), 1) as min_temp
                FROM cities c 
                JOIN weather_data w ON c.id = w.city_id 
                WHERE w.date >= date('now', '-7 days')
                GROUP BY c.id, c.name, c.country
                ORDER BY avg_temp DESC
                LIMIT 5
            """,
            "explanation": "Compare average temperatures across cities in the past week"
        },
        {
            "name": "Cities with free attractions",
            "query": """
                SELECT 
                    c.name as city,
                    c.country,
                    COUNT(td.id) as free_attractions,
                    GROUP_CONCAT(td.attraction_name, ', ') as attractions
                FROM cities c 
                JOIN travel_destinations td ON c.id = td.city_id 
                WHERE td.cost_level = 'Free'
                GROUP BY c.id, c.name, c.country
                ORDER BY free_attractions DESC
            """,
            "explanation": "Find cities with the most free attractions"
        }
    ]
    
    for i, query_test in enumerate(complex_queries, 1):
        print(f"\n{i}. {query_test['name']}:")
        
        try:
            sql_data = {
                "tool_name": "query_weather_database",
                "parameters": {
                    "sql_query": query_test["query"],
                    "explanation": query_test["explanation"]
                }
            }
            response = requests.post(f"{server_url}/execute", json=sql_data)
            result = response.json()["result"]
            
            if result["execution_status"] == "success":
                print(f"   ✅ Found {result['row_count']} results")
                # Show first 2 results
                for row in result['results'][:2]:
                    print(f"      {json.dumps(row, indent=8)}")
            else:
                print(f"   ❌ Query failed: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n✅ Complex query tests completed!")


def demo_example_interactions():
    """Show example interactions that users can try."""
    
    print("\n🎯 Example Interactions to Try:")
    print("=" * 50)
    
    examples = [
        {
            "question": "What's the weather like in Tokyo recently?",
            "expected": "Should query recent weather data for Tokyo and provide temperature, conditions, etc."
        },
        {
            "question": "Which cities have the highest population?",
            "expected": "Should query cities table ordered by population"
        },
        {
            "question": "Show me attractions in Paris that are free",
            "expected": "Should join cities and travel_destinations tables filtering for Paris and free attractions"
        },
        {
            "question": "Compare the temperature between New York and London",
            "expected": "Should query weather data for both cities and compare average temperatures"
        },
        {
            "question": "Which city had the most rain in the past week?",
            "expected": "Should aggregate precipitation data and find the city with highest rainfall"
        },
        {
            "question": "Find me tropical cities with good attractions",
            "expected": "Should combine weather patterns and attraction data to find warm cities with high-rated destinations"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. User: \"{example['question']}\"")
        print(f"   Expected: {example['expected']}")
    
    print(f"\n💡 To test these, run:")
    print(f"   python advanced_mcp_client.py")
    print(f"   (Make sure the server is running first!)")


def main():
    """Run all tests for the advanced MCP implementation."""
    
    print("🚀 Advanced MCP Implementation Test Suite")
    print("=" * 60)
    
    # Test 1: Database setup
    db_success = test_database_setup()
    
    # Test 2: Advanced MCP Server
    server_success = test_advanced_mcp_server()
    
    # Test 3: Complex queries (only if server is working)
    if server_success:
        test_complex_queries()
    
    # Test 4: Show example interactions
    demo_example_interactions()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"   Database Setup: {'✅ PASS' if db_success else '❌ FAIL'}")
    print(f"   MCP Server: {'✅ PASS' if server_success else '❌ FAIL'}")
    
    if db_success and server_success:
        print("\n🎉 All tests passed! Your advanced MCP implementation is ready.")
        print("\n🚀 To start using it:")
        print("   1. Terminal 1: python advanced_mcp_server.py")
        print("   2. Terminal 2: python advanced_mcp_client.py")
        print("   3. Ask natural language questions about weather and travel data!")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    main()