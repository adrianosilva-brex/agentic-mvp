"""
Simple MCP Client that interacts with the LLM Gateway
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.llm_gateway_interface import send_message
import json
from typing import Dict, Any, List


class SimpleMCPClient:
    """A simple MCP client that uses tools with the LLM Gateway."""
    
    def __init__(self, provider: str = "anthropic", model_id: str = "claude-3-5-sonnet-20241022"):
        self.provider = provider
        self.model_id = model_id
        self.tools = []
        self.register_default_tools()
    
    def register_default_tools(self):
        """Register some basic tools for demonstration."""
        self.tools = [
            {
                "name": "get_weather",
                "description": "Get current weather for a location",
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
                            "description": "Temperature units",
                            "default": "celsius"
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "calculate",
                "description": "Perform basic mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string", 
                            "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 3')"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "get_trip_info",
                "description": "Get information about a trip destination",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "destination": {
                            "type": "string",
                            "description": "The destination city or country"
                        },
                        "info_type": {
                            "type": "string",
                            "enum": ["attractions", "weather", "culture", "food"],
                            "description": "Type of information to retrieve"
                        }
                    },
                    "required": ["destination"]
                }
            }
        ]
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return available tools."""
        return self.tools
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call and return results."""
        
        if tool_name == "get_weather":
            location = parameters.get("location", "Unknown")
            units = parameters.get("units", "celsius")
            temp = "22°C" if units == "celsius" else "72°F"
            return {
                "location": location,
                "temperature": temp,
                "condition": "Partly cloudy",
                "humidity": "65%",
                "units": units
            }
        
        elif tool_name == "calculate":
            expression = parameters.get("expression", "")
            try:
                # Simple and safe evaluation for basic math
                result = eval(expression, {"__builtins__": {}}, {})
                return {
                    "expression": expression,
                    "result": result
                }
            except Exception as e:
                return {
                    "expression": expression,
                    "error": f"Calculation error: {str(e)}"
                }
        
        elif tool_name == "get_trip_info":
            destination = parameters.get("destination", "Unknown")
            info_type = parameters.get("info_type", "attractions")
            
            # Mock trip information
            trip_data = {
                "destination": destination,
                "info_type": info_type,
                "data": {
                    "attractions": [f"{destination} Museum", f"{destination} Park", f"Historic {destination} Center"],
                    "weather": f"{destination} typically has mild weather year-round",
                    "culture": f"{destination} has a rich cultural heritage with local traditions",
                    "food": f"Local cuisine in {destination} includes traditional dishes and local specialties"
                }.get(info_type, f"General information about {destination}")
            }
            
            return trip_data
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def chat_with_tools(self, user_message: str) -> str:
        """Send a message to the LLM with available tools."""
        
        # For this simple implementation, we'll use a basic approach
        # In a real MCP implementation, this would be more sophisticated
        
        system_message = f"""You are a helpful assistant with access to the following tools:

{json.dumps(self.tools, indent=2)}

When you need to use a tool, respond with a JSON object in this format:
{{"tool_call": {{"name": "tool_name", "parameters": {{"param1": "value1"}}}}}}

If you don't need to use a tool, just respond normally.
"""
        
        try:
            # Send message to LLM
            response = send_message(self.provider, self.model_id, f"System: {system_message}\n\nUser: {user_message}")
            
            # Extract content based on provider
            if self.provider == "anthropic":
                content = response["content"][0]["text"]
            else:
                content = response["choices"][0]["message"]["content"]
            
            # Check if the response contains a tool call
            if "tool_call" in content and "{" in content:
                try:
                    # Extract JSON from response
                    start = content.find('{"tool_call"')
                    end = content.rfind('}') + 1
                    if start != -1 and end != -1:
                        tool_call_json = content[start:end]
                        tool_call = json.loads(tool_call_json)
                        
                        if "tool_call" in tool_call:
                            tool_name = tool_call["tool_call"]["name"]
                            parameters = tool_call["tool_call"]["parameters"]
                            
                            # Execute the tool
                            tool_result = self.execute_tool(tool_name, parameters)
                            
                            # Send tool result back to LLM for final response
                            follow_up = f"Tool '{tool_name}' returned: {json.dumps(tool_result, indent=2)}\n\nPlease provide a natural language response to the user based on this information."
                            
                            final_response = send_message(self.provider, self.model_id, follow_up)
                            
                            if self.provider == "anthropic":
                                return final_response["content"][0]["text"]
                            else:
                                return final_response["choices"][0]["message"]["content"]
                
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error parsing tool call: {e}")
                    return content
            
            return content
            
        except Exception as e:
            return f"Error communicating with LLM: {str(e)}"


def main():
    """Simple test of the MCP client."""
    client = SimpleMCPClient()
    
    print("🤖 Simple MCP Client Test")
    print("Available tools:", [tool["name"] for tool in client.get_tools()])
    print("\nTry asking about:")
    print("- Weather: 'What's the weather in New York?'")
    print("- Math: 'Calculate 15 * 24'")
    print("- Travel: 'Tell me about attractions in Paris'")
    print("- Or just chat normally!")
    print("\nType 'quit' to exit\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        print("🤖 Assistant:", end=" ")
        response = client.chat_with_tools(user_input)
        print(response)
        print()


if __name__ == "__main__":
    main()