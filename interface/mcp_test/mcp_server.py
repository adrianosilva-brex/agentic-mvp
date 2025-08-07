"""
Simple MCP Server implementation for testing with the LLM Gateway
"""

from flask import Flask, request, jsonify
from typing import Dict, Any, List
import json


class SimpleMCPServer:
    """A simple MCP server that provides tools for the LLM Gateway."""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.tools = self._initialize_tools()
        self._setup_routes()
    
    def _initialize_tools(self) -> List[Dict[str, Any]]:
        """Initialize the tools this MCP server provides."""
        return [
            {
                "name": "get_weather",
                "description": "Get current weather information for a location",
                "type": "function",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        },
                        "units": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "Temperature units"
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "trip_calculator",
                "description": "Calculate trip costs and duration",
                "type": "function", 
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_city": {
                            "type": "string",
                            "description": "Origin city"
                        },
                        "to_city": {
                            "type": "string", 
                            "description": "Destination city"
                        },
                        "travel_type": {
                            "type": "string",
                            "enum": ["flight", "train", "car"],
                            "description": "Type of travel"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days for the trip",
                            "minimum": 1
                        }
                    },
                    "required": ["from_city", "to_city", "travel_type"]
                }
            },
            {
                "name": "currency_converter",
                "description": "Convert currency amounts",
                "type": "function",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "number",
                            "description": "Amount to convert"
                        },
                        "from_currency": {
                            "type": "string",
                            "description": "Source currency code (e.g., USD)"
                        },
                        "to_currency": {
                            "type": "string", 
                            "description": "Target currency code (e.g., EUR)"
                        }
                    },
                    "required": ["amount", "from_currency", "to_currency"]
                }
            }
        ]
    
    def _setup_routes(self):
        """Setup Flask routes for the MCP server."""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({"status": "healthy", "server": "Simple MCP Server"})
        
        @self.app.route('/tools', methods=['GET'])
        def list_tools():
            """List available tools."""
            return jsonify({"tools": self.tools})
        
        @self.app.route('/tools/<tool_name>/execute', methods=['POST'])
        def execute_tool(tool_name: str):
            """Execute a specific tool."""
            try:
                data = request.get_json()
                parameters = data.get('parameters', {})
                
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
                    "error": str(e),
                    "tool_name": tool_name
                }), 400
        
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
    
    def _execute_tool_function(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual tool function."""
        
        if tool_name == "get_weather":
            location = parameters.get("location", "Unknown")
            units = parameters.get("units", "celsius")
            
            # Mock weather data
            temp_c = 22
            temp_f = int(temp_c * 9/5 + 32)
            temp = f"{temp_c}°C" if units == "celsius" else f"{temp_f}°F"
            
            return {
                "location": location,
                "temperature": temp,
                "condition": "Partly cloudy",
                "humidity": "65%",
                "wind": "10 km/h",
                "units": units
            }
        
        elif tool_name == "trip_calculator":
            from_city = parameters.get("from_city", "Unknown")
            to_city = parameters.get("to_city", "Unknown")
            travel_type = parameters.get("travel_type", "flight")
            days = parameters.get("days", 3)
            
            # Mock trip calculation
            base_costs = {"flight": 500, "train": 200, "car": 150}
            base_cost = base_costs.get(travel_type, 300)
            
            # Add daily costs
            daily_cost = 120  # hotel + food
            total_cost = base_cost + (daily_cost * days)
            
            durations = {"flight": "3 hours", "train": "8 hours", "car": "12 hours"}
            duration = durations.get(travel_type, "Variable")
            
            return {
                "from_city": from_city,
                "to_city": to_city,
                "travel_type": travel_type,
                "days": days,
                "estimated_cost": f"${total_cost}",
                "travel_duration": duration,
                "breakdown": {
                    "transportation": f"${base_cost}",
                    "accommodation_food": f"${daily_cost * days}",
                    "daily_rate": f"${daily_cost}/day"
                }
            }
        
        elif tool_name == "currency_converter":
            amount = parameters.get("amount", 0)
            from_currency = parameters.get("from_currency", "USD").upper()
            to_currency = parameters.get("to_currency", "EUR").upper()
            
            # Mock exchange rates
            rates = {
                ("USD", "EUR"): 0.85,
                ("EUR", "USD"): 1.18,
                ("USD", "GBP"): 0.75,
                ("GBP", "USD"): 1.33,
                ("EUR", "GBP"): 0.88,
                ("GBP", "EUR"): 1.14
            }
            
            if from_currency == to_currency:
                converted_amount = amount
                rate = 1.0
            else:
                rate = rates.get((from_currency, to_currency), 1.0)
                converted_amount = round(amount * rate, 2)
            
            return {
                "original_amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "converted_amount": converted_amount,
                "exchange_rate": rate,
                "formatted": f"{amount} {from_currency} = {converted_amount} {to_currency}"
            }
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    def run(self, host='localhost', port=5000, debug=True):
        """Run the MCP server."""
        print(f"🚀 Starting Simple MCP Server on http://{host}:{port}")
        print("Available tools:", [tool["name"] for tool in self.tools])
        print("Endpoints:")
        print(f"  - GET  http://{host}:{port}/health")
        print(f"  - GET  http://{host}:{port}/tools")
        print(f"  - POST http://{host}:{port}/execute")
        print(f"  - POST http://{host}:{port}/tools/<tool_name>/execute")
        
        self.app.run(host=host, port=port, debug=debug)


def main():
    """Run the MCP server."""
    server = SimpleMCPServer()
    server.run()


if __name__ == "__main__":
    main()