"""
Advanced MCP Server with SQLite database integration
"""

from flask import Flask, request, jsonify
from typing import Dict, Any, List
import json
import re
from database import WeatherDatabase


class AdvancedMCPServer:
    """Advanced MCP server with SQL query capabilities."""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.db = WeatherDatabase()
        self.tools = self._initialize_tools()
        self._setup_routes()
    
    def _initialize_tools(self) -> List[Dict[str, Any]]:
        """Initialize the tools this MCP server provides."""
        return [
            {
                "name": "query_weather_database",
                "description": "Query the weather database using SQL. Can search weather data, cities, and travel destinations.",
                "type": "function",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql_query": {
                            "type": "string",
                            "description": "SQL query to execute. Use SELECT statements only. Available tables: cities, weather_data, travel_destinations"
                        },
                        "explanation": {
                            "type": "string",
                            "description": "Brief explanation of what this query is trying to find"
                        }
                    },
                    "required": ["sql_query"]
                }
            },
            {
                "name": "get_database_schema",
                "description": "Get information about the database structure and available tables/columns",
                "type": "function",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Optional: specific table to get schema for. If not provided, returns all tables"
                        }
                    }
                }
            },
            {
                "name": "suggest_sql_query",
                "description": "Get SQL query suggestions based on natural language description",
                "type": "function",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Natural language description of what you want to find"
                        }
                    },
                    "required": ["description"]
                }
            },
            {
                "name": "get_weather_summary",
                "description": "Get a weather summary for a specific city or region",
                "type": "function",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city_name": {
                            "type": "string",
                            "description": "Name of the city"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of recent days to include (default: 7)",
                            "default": 7
                        }
                    },
                    "required": ["city_name"]
                }
            }
        ]
    
    def _setup_routes(self):
        """Setup Flask routes for the MCP server."""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({"status": "healthy", "server": "Advanced MCP Server with Database"})
        
        @self.app.route('/tools', methods=['GET'])
        def list_tools():
            """List available tools."""
            return jsonify({"tools": self.tools})
        
        @self.app.route('/execute', methods=['POST'])
        def execute_any_tool():
            """Execute any tool by name in the request body."""
            try:
                data = request.get_json()
                tool_name = data.get('tool_name')
                parameters = data.get('parameters', {})
                
                if not tool_name:
                    return jsonify({"success": False, "error": "tool_name is required"}), 400
                
                result = self._execute_tool_function(tool_name, parameters)
                
                return jsonify({
                    "success": True,
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "result": result
                })
                
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 400
    
    def _validate_sql_query(self, query: str) -> bool:
        """Validate that the SQL query is safe (SELECT only)."""
        # Remove comments and normalize whitespace
        cleaned_query = re.sub(r'--.*?\n', '', query)
        cleaned_query = re.sub(r'/\*.*?\*/', '', cleaned_query, flags=re.DOTALL)
        cleaned_query = cleaned_query.strip().upper()
        
        # Only allow SELECT statements
        if not cleaned_query.startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")
        
        # Block dangerous keywords
        dangerous_keywords = ['DELETE', 'DROP', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'EXEC', 'EXECUTE']
        for keyword in dangerous_keywords:
            if keyword in cleaned_query:
                raise ValueError(f"Keyword '{keyword}' is not allowed")
        
        return True
    
    def _execute_tool_function(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual tool function."""
        
        if tool_name == "query_weather_database":
            sql_query = parameters.get("sql_query", "")
            explanation = parameters.get("explanation", "")
            
            # Validate the query
            self._validate_sql_query(sql_query)
            
            try:
                results = self.db.execute_query(sql_query)
                
                return {
                    "query": sql_query,
                    "explanation": explanation,
                    "row_count": len(results),
                    "results": results[:50],  # Limit results to prevent huge responses
                    "truncated": len(results) > 50,
                    "execution_status": "success"
                }
            
            except Exception as e:
                return {
                    "query": sql_query,
                    "explanation": explanation,
                    "error": str(e),
                    "execution_status": "error"
                }
        
        elif tool_name == "get_database_schema":
            table_name = parameters.get("table_name")
            
            schema_info = self.db.get_schema_info()
            
            if table_name:
                if table_name in schema_info:
                    return {
                        "table": table_name,
                        "schema": schema_info[table_name]
                    }
                else:
                    return {
                        "error": f"Table '{table_name}' not found",
                        "available_tables": list(schema_info.keys())
                    }
            else:
                return {
                    "all_tables": schema_info,
                    "table_count": len(schema_info)
                }
        
        elif tool_name == "suggest_sql_query":
            description = parameters.get("description", "")
            
            # Generate SQL suggestions based on description
            suggestions = self._generate_sql_suggestions(description.lower())
            
            return {
                "description": description,
                "suggestions": suggestions,
                "note": "These are suggestions - you may need to modify them based on your specific needs"
            }
        
        elif tool_name == "get_weather_summary":
            city_name = parameters.get("city_name", "")
            days = parameters.get("days", 7)
            
            try:
                # Get weather summary for the city
                weather_query = """
                    SELECT 
                        c.name as city,
                        c.country,
                        AVG(w.temperature_celsius) as avg_temp_c,
                        MAX(w.temperature_celsius) as max_temp_c,
                        MIN(w.temperature_celsius) as min_temp_c,
                        AVG(w.humidity) as avg_humidity,
                        SUM(w.precipitation_mm) as total_precipitation,
                        COUNT(*) as data_points,
                        w.condition as latest_condition
                    FROM cities c 
                    JOIN weather_data w ON c.id = w.city_id 
                    WHERE c.name LIKE ? 
                    AND w.date >= date('now', '-{} days')
                    GROUP BY c.id, c.name, c.country
                    ORDER BY w.date DESC
                    LIMIT 1
                """.format(days)
                
                results = self.db.execute_query(weather_query, (f"%{city_name}%",))
                
                if results:
                    result = results[0]
                    return {
                        "city": result["city"],
                        "country": result["country"],
                        "period": f"Last {days} days",
                        "summary": {
                            "avg_temperature": f"{result['avg_temp_c']:.1f}°C",
                            "temperature_range": f"{result['min_temp_c']:.1f}°C to {result['max_temp_c']:.1f}°C",
                            "avg_humidity": f"{result['avg_humidity']:.0f}%",
                            "total_precipitation": f"{result['total_precipitation']:.1f}mm",
                            "latest_condition": result["latest_condition"],
                            "data_points": result["data_points"]
                        }
                    }
                else:
                    return {
                        "error": f"No weather data found for city: {city_name}",
                        "suggestion": "Try a different city name or check the available cities"
                    }
            
            except Exception as e:
                return {
                    "error": f"Error getting weather summary: {str(e)}"
                }
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    def _generate_sql_suggestions(self, description: str) -> List[Dict[str, str]]:
        """Generate SQL query suggestions based on natural language description."""
        
        suggestions = []
        
        # Weather-related queries
        if any(word in description for word in ['weather', 'temperature', 'rain', 'humidity', 'wind']):
            suggestions.append({
                "title": "Recent weather for a city",
                "query": "SELECT c.name, w.date, w.temperature_celsius, w.condition, w.humidity FROM cities c JOIN weather_data w ON c.id = w.city_id WHERE c.name = 'Tokyo' ORDER BY w.date DESC LIMIT 7"
            })
            
            suggestions.append({
                "title": "Average temperature by city",
                "query": "SELECT c.name, c.country, AVG(w.temperature_celsius) as avg_temp FROM cities c JOIN weather_data w ON c.id = w.city_id GROUP BY c.id, c.name, c.country ORDER BY avg_temp DESC"
            })
        
        # Location/city queries
        if any(word in description for word in ['city', 'cities', 'location', 'place']):
            suggestions.append({
                "title": "Cities by population",
                "query": "SELECT name, country, population FROM cities ORDER BY population DESC LIMIT 10"
            })
            
            suggestions.append({
                "title": "Cities in a specific country",
                "query": "SELECT name, state, population, timezone FROM cities WHERE country = 'United States'"
            })
        
        # Travel/attraction queries
        if any(word in description for word in ['travel', 'attraction', 'destination', 'visit', 'tourism']):
            suggestions.append({
                "title": "Top attractions by rating",
                "query": "SELECT c.name as city, td.attraction_name, td.category, td.rating FROM cities c JOIN travel_destinations td ON c.id = td.city_id ORDER BY td.rating DESC LIMIT 10"
            })
            
            suggestions.append({
                "title": "Free attractions",
                "query": "SELECT c.name as city, td.attraction_name, td.description FROM cities c JOIN travel_destinations td ON c.id = td.city_id WHERE td.cost_level = 'Free'"
            })
        
        # Comparison queries
        if any(word in description for word in ['compare', 'comparison', 'vs', 'versus', 'between']):
            suggestions.append({
                "title": "Compare weather between cities",
                "query": "SELECT c.name, AVG(w.temperature_celsius) as avg_temp, AVG(w.humidity) as avg_humidity FROM cities c JOIN weather_data w ON c.id = w.city_id WHERE c.name IN ('Tokyo', 'New York', 'London') GROUP BY c.name"
            })
        
        # If no specific suggestions, provide general ones
        if not suggestions:
            suggestions = [
                {
                    "title": "All cities overview",
                    "query": "SELECT name, country, population FROM cities ORDER BY population DESC"
                },
                {
                    "title": "Recent weather data",
                    "query": "SELECT c.name, w.date, w.temperature_celsius, w.condition FROM cities c JOIN weather_data w ON c.id = w.city_id ORDER BY w.date DESC LIMIT 20"
                },
                {
                    "title": "Top rated attractions",
                    "query": "SELECT c.name as city, td.attraction_name, td.rating FROM cities c JOIN travel_destinations td ON c.id = td.city_id ORDER BY td.rating DESC LIMIT 10"
                }
            ]
        
        return suggestions
    
    def run(self, host='localhost', port=5001, debug=True):
        """Run the advanced MCP server."""
        print(f"🚀 Starting Advanced MCP Server with Database on http://{host}:{port}")
        print("Available tools:", [tool["name"] for tool in self.tools])
        print("Database tables:", list(self.db.get_schema_info().keys()))
        print("Endpoints:")
        print(f"  - GET  http://{host}:{port}/health")
        print(f"  - GET  http://{host}:{port}/tools")
        print(f"  - POST http://{host}:{port}/execute")
        
        self.app.run(host=host, port=port, debug=debug)


def main():
    """Run the advanced MCP server."""
    server = AdvancedMCPServer()
    server.run()


if __name__ == "__main__":
    main()