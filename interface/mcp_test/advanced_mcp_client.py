"""
Advanced MCP Client with detailed thinking process display
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.llm_gateway_interface import send_message
import json
import requests
import time
from typing import Dict, Any, List
from datetime import datetime
import re


class AdvancedMCPClient:
    """Advanced MCP client that shows LLM thinking process and database integration."""
    
    def __init__(self, provider: str = "anthropic", model_id: str = "claude-3-5-sonnet-20241022", 
                 mcp_server_url: str = "http://localhost:5001"):
        self.provider = provider
        self.model_id = model_id
        self.mcp_server_url = mcp_server_url
        self.tools = []
        self.thinking_steps = []
        self.load_tools_from_server()
    
    def load_tools_from_server(self):
        """Load available tools from the MCP server."""
        try:
            response = requests.get(f"{self.mcp_server_url}/tools")
            if response.status_code == 200:
                self.tools = response.json()["tools"]
                print(f"✅ Loaded {len(self.tools)} tools from MCP server")
            else:
                print(f"⚠️  Could not load tools from MCP server: {response.status_code}")
                self.tools = []
        except Exception as e:
            print(f"⚠️  Could not connect to MCP server: {e}")
            self.tools = []
    
    def add_thinking_step(self, step_type: str, content: str, data: Any = None):
        """Add a thinking step for display."""
        self.thinking_steps.append({
            "timestamp": datetime.now().isoformat(),
            "type": step_type,
            "content": content,
            "data": data
        })
    
    def _extract_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """Extract all tool calls from LLM response content."""
        tool_calls = []
        
        # Find all JSON objects that contain tool_call using a more robust approach
        try:
            # Split content by lines and look for tool_call patterns
            lines = content.split('\n')
            current_json = ""
            in_json = False
            brace_count = 0
            
            for line in lines:
                line = line.strip()
                if '{"tool_call"' in line or in_json:
                    in_json = True
                    current_json += line + "\n"
                    
                    # Count braces to find complete JSON objects
                    for char in line:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                    
                    # When we have a complete JSON object
                    if brace_count == 0 and current_json.strip():
                        try:
                            # Clean up the JSON string
                            json_str = current_json.strip()
                            if json_str.endswith(','):
                                json_str = json_str[:-1]
                            
                            tool_call_obj = json.loads(json_str)
                            if "tool_call" in tool_call_obj:
                                tool_call_data = tool_call_obj["tool_call"]
                                if "name" in tool_call_data and "parameters" in tool_call_data:
                                    tool_calls.append({
                                        "name": tool_call_data["name"],
                                        "parameters": tool_call_data["parameters"]
                                    })
                        except json.JSONDecodeError:
                            pass
                        
                        # Reset for next JSON object
                        current_json = ""
                        in_json = False
                        brace_count = 0
            
            # Fallback: try regex approach if the above didn't work
            if not tool_calls:
                pattern = r'\{"tool_call":\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\}'
                matches = re.findall(pattern, content, re.DOTALL)
                
                for match in matches:
                    try:
                        tool_call_obj = json.loads(match)
                        if "tool_call" in tool_call_obj:
                            tool_call_data = tool_call_obj["tool_call"]
                            if "name" in tool_call_data and "parameters" in tool_call_data:
                                tool_calls.append({
                                    "name": tool_call_data["name"],
                                    "parameters": tool_call_data["parameters"]
                                })
                    except json.JSONDecodeError:
                        continue
            
        except Exception as e:
            print(f"Warning: Error extracting tool calls: {e}")
        
        return tool_calls
    
    def display_thinking_step(self, step_type: str, content: str, data: Any = None):
        """Display a thinking step in real-time."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        icons = {
            "user_input": "👤",
            "thinking": "🤔",
            "tool_selection": "🔧",
            "tool_execution": "⚡",
            "sql_query": "🗃️",
            "results": "📊",
            "response": "🤖",
            "error": "❌"
        }
        
        icon = icons.get(step_type, "ℹ️")
        print(f"\n{icon} [{timestamp}] {content}")
        
        if data and step_type in ["sql_query", "results", "tool_execution"]:
            if isinstance(data, dict):
                if step_type == "sql_query":
                    print(f"   📝 Query: {data.get('query', 'N/A')}")
                    if data.get('explanation'):
                        print(f"   💭 Purpose: {data['explanation']}")
                elif step_type == "results":
                    row_count = data.get('row_count', 0)
                    print(f"   📊 Found {row_count} rows")
                    if row_count > 0 and 'results' in data:
                        print(f"   🔍 Sample: {json.dumps(data['results'][:2], indent=6)}")
                elif step_type == "tool_execution":
                    print(f"   🛠️  Tool: {data.get('tool_name')}")
                    if data.get('parameters'):
                        print(f"   ⚙️  Params: {json.dumps(data['parameters'], indent=6)}")
        
        self.add_thinking_step(step_type, content, data)
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on the MCP server."""
        try:
            self.display_thinking_step("tool_execution", f"Executing tool: {tool_name}", {
                "tool_name": tool_name,
                "parameters": parameters
            })
            
            response = requests.post(f"{self.mcp_server_url}/execute", json={
                "tool_name": tool_name,
                "parameters": parameters
            })
            
            if response.status_code == 200:
                result = response.json()["result"]
                
                if tool_name == "query_weather_database":
                    self.display_thinking_step("sql_query", "SQL query executed", {
                        "query": result.get("query"),
                        "explanation": result.get("explanation")
                    })
                    self.display_thinking_step("results", "Database results retrieved", result)
                
                return result
            else:
                error_msg = f"Tool execution failed: {response.status_code}"
                self.display_thinking_step("error", error_msg)
                return {"error": error_msg}
        
        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            self.display_thinking_step("error", error_msg)
            return {"error": error_msg}
    
    def chat_with_database(self, user_message: str) -> str:
        """Send a message to the LLM with database tools available."""
        
        self.thinking_steps = []  # Reset thinking steps
        self.display_thinking_step("user_input", f"User asks: {user_message}")
        
        # Enhanced system message with database schema info
        schema_info = self.execute_tool("get_database_schema", {})
        
        system_message = f"""You are a helpful assistant with access to a weather and travel database. You can query the database using SQL to answer questions about weather, cities, and travel destinations.

Available tools:
{json.dumps(self.tools, indent=2)}

Database Schema:
{json.dumps(schema_info, indent=2)}

When you need to query the database, respond with a JSON object in this format:
{{"tool_call": {{"name": "query_weather_database", "parameters": {{"sql_query": "SELECT ...", "explanation": "Brief explanation of what this query finds"}}}}}}

IMPORTANT: 
- Try to answer questions with a SINGLE comprehensive SQL query when possible (using JOINs, subqueries, etc.)
- Only use multiple tool calls if the question truly requires separate, unrelated queries
- The query_weather_database tool can access all tables (cities, weather_data, travel_destinations)

You can also use other tools:
- get_database_schema: Get information about available tables and columns
- suggest_sql_query: Get SQL suggestions based on natural language  
- get_weather_summary: Get a quick weather summary for a city

Always explain your thought process and what you found in the data.
"""
        
        try:
            self.display_thinking_step("thinking", "Sending question to LLM with database tools...")
            
            # First LLM call
            response = send_message(self.provider, self.model_id, f"System: {system_message}\n\nUser: {user_message}")
            
            # Extract content based on provider
            if self.provider == "anthropic":
                content = response["content"][0]["text"]
            else:
                content = response["choices"][0]["message"]["content"]
            
            self.display_thinking_step("thinking", "LLM responded, checking for tool calls...")
            
            # Check if the response contains tool calls
            if "tool_call" in content and "{" in content:
                try:
                    # Extract all tool calls from the response
                    tool_calls = self._extract_tool_calls(content)
                    
                    if tool_calls:
                        all_tool_results = []
                        
                        # Execute each tool call
                        for i, tool_call in enumerate(tool_calls):
                            tool_name = tool_call["name"]
                            parameters = tool_call["parameters"]
                            
                            self.display_thinking_step("tool_selection", f"LLM decided to use tool {i+1}/{len(tool_calls)}: {tool_name}")
                            
                            # Execute the tool
                            tool_result = self.execute_tool(tool_name, parameters)
                            all_tool_results.append({
                                "tool_name": tool_name,
                                "parameters": parameters,
                                "result": tool_result
                            })
                        
                        # Send all tool results back to LLM for final response
                        results_summary = "\n\n".join([
                            f"Tool '{result['tool_name']}' with parameters {json.dumps(result['parameters'], indent=2)} returned:\n{json.dumps(result['result'], indent=2)}"
                            for result in all_tool_results
                        ])
                        
                        follow_up = f"""The following tools were executed with these results:

{results_summary}

Please provide a comprehensive, natural language response to the user based on all this data. Include:
1. A direct answer to their question
2. Key insights from the data
3. Any interesting patterns or details
4. Suggestions for related information they might find useful

Make the response conversational and easy to understand, integrating information from all the tool results."""
                        
                        self.display_thinking_step("thinking", f"Sending {len(all_tool_results)} tool results back to LLM for final response...")
                        
                        final_response = send_message(self.provider, self.model_id, follow_up)
                        
                        if self.provider == "anthropic":
                            final_content = final_response["content"][0]["text"]
                        else:
                            final_content = final_response["choices"][0]["message"]["content"]
                        
                        self.display_thinking_step("response", "Final response generated")
                        return final_content
                
                except (json.JSONDecodeError, KeyError) as e:
                    self.display_thinking_step("error", f"Error parsing tool call: {e}")
                    return content
            
            # If no tool call, return the direct response
            self.display_thinking_step("response", "Direct response (no tools needed)")
            return content
            
        except Exception as e:
            error_msg = f"Error communicating with LLM: {str(e)}"
            self.display_thinking_step("error", error_msg)
            return error_msg
    
    def get_thinking_summary(self) -> str:
        """Get a summary of the thinking process."""
        if not self.thinking_steps:
            return "No thinking steps recorded."
        
        summary = "\n📋 Thinking Process Summary:\n"
        for i, step in enumerate(self.thinking_steps, 1):
            summary += f"{i}. {step['type']}: {step['content']}\n"
        
        return summary


def main():
    """Interactive CLI for the advanced MCP client."""
    print("🧠 Advanced MCP Client with Database Integration")
    print("=" * 60)
    
    # Initialize client
    client = AdvancedMCPClient()
    
    if not client.tools:
        print("❌ Could not connect to MCP server. Make sure it's running on http://localhost:5001")
        print("   Start it with: python advanced_mcp_server.py")
        return
    
    print(f"✅ Connected to MCP server with {len(client.tools)} tools")
    print("\nAvailable tools:")
    for tool in client.tools:
        print(f"  🔧 {tool['name']}: {tool['description']}")
    
    print("\n💡 Try asking about:")
    print("  - Weather: 'What's the weather like in Tokyo recently?'")
    print("  - Comparisons: 'Compare the temperature between New York and London'")
    print("  - Travel: 'Show me the top rated attractions in Paris'")
    print("  - Cities: 'Which cities have the highest population?'")
    print("  - Complex queries: 'Find cities with recent rain and their attractions'")
    print("\nType 'help' for more examples, 'summary' for thinking process, 'quit' to exit\n")
    
    while True:
        try:
            user_input = input("🔍 Ask about weather/travel data: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == 'help':
                print("\n📚 Example queries:")
                print("  • 'What was the weather in Sydney last week?'")
                print("  • 'Show me all cities in Japan'")
                print("  • 'Which city had the most rain recently?'")
                print("  • 'List attractions in London that are free'")
                print("  • 'Compare humidity levels between tropical cities'")
                print("  • 'Find the coldest and warmest cities in the database'")
                continue
            
            if user_input.lower() == 'summary':
                print(client.get_thinking_summary())
                continue
            
            if not user_input:
                continue
            
            print("\n" + "="*80)
            start_time = time.time()
            
            # Process the query
            response = client.chat_with_database(user_input)
            
            end_time = time.time()
            
            print("\n" + "="*80)
            print("🤖 Final Response:")
            print(response)
            print(f"\n⏱️  Total processing time: {end_time - start_time:.2f} seconds")
            print("="*80)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()