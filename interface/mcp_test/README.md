# Simple MCP (Model Context Protocol) Implementation

This is a basic MCP implementation that demonstrates how to create tools that can be used by LLMs through the LLM Gateway.

## Files

- `mcp_server.py` - Simple MCP server with tools (weather, trip calculator, currency converter)
- `mcp_client.py` - MCP client that integrates tools with LLM calls
- `test_mcp.py` - Test suite for both server and client
- `README.md` - This file

## Prerequisites

1. **Virtual Environment**: Make sure you're in the activated virtual environment:
   ```bash
   cd /Users/adriano.silva/exp-trip/trip-mvp
   source venv/bin/activate
   ```

2. **Dependencies**: Install required packages:
   ```bash
   pip install flask requests python-dotenv
   ```

3. **Environment Variables**: Make sure your `.env` file has:
   ```
   BREX_LLM_GATEWAY_URL=http://localhost:8080/gateway/
   ```

## Testing Instructions

### 1. Test the MCP Server (Standalone)

Start the MCP server in one terminal:

```bash
cd /Users/adriano.silva/exp-trip/trip-mvp/interface/mcp_test
python mcp_server.py
```

This will start the server on `http://localhost:5000` with endpoints:
- `GET /health` - Health check
- `GET /tools` - List available tools
- `POST /execute` - Execute any tool
- `POST /tools/<tool_name>/execute` - Execute specific tool

### 2. Test the MCP Client (With LLM Integration)

In another terminal, test the client:

```bash
cd /Users/adriano.silva/exp-trip/trip-mvp/interface/mcp_test
python mcp_client.py
```

Try these example queries:
- "What's the weather in New York?"
- "Calculate 15 * 24"
- "Tell me about attractions in Paris"

### 3. Run the Complete Test Suite

Run the automated test suite:

```bash
cd /Users/adriano.silva/exp-trip/trip-mvp/interface/mcp_test
python test_mcp.py
```

This will:
1. Test all MCP server endpoints
2. Test MCP client with LLM integration
3. Optionally register the server with the LLM Gateway

### 4. Manual API Testing

You can also test the MCP server manually with curl:

```bash
# Health check
curl -X GET http://localhost:5000/health

# List tools
curl -X GET http://localhost:5000/tools

# Test weather tool
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "get_weather",
    "parameters": {
      "location": "San Francisco, CA",
      "units": "celsius"
    }
  }'

# Test trip calculator
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "trip_calculator",
    "parameters": {
      "from_city": "New York",
      "to_city": "London", 
      "travel_type": "flight",
      "days": 7
    }
  }'

# Test currency converter
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "currency_converter",
    "parameters": {
      "amount": 500,
      "from_currency": "USD",
      "to_currency": "EUR"
    }
  }'
```

### 5. Register with LLM Gateway (Optional)

If you have the LLM Gateway running, you can register the MCP server:

```bash
# Register MCP server
curl -X POST http://localhost:8080/mcp-servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Simple Trip MCP Server",
    "url": "http://localhost:5000",
    "authentication_secret_key": "demo_secret_key"
  }'

# List tools of registered server (replace {server_id} with actual ID)
curl -X GET http://localhost:8080/mcp-servers/{server_id}/tools
```

## How It Works

### MCP Server (`mcp_server.py`)
- Provides 3 tools: weather, trip calculator, currency converter
- Exposes REST API endpoints for tool execution
- Returns mock data for demonstration

### MCP Client (`mcp_client.py`)
- Integrates tools with LLM calls through the LLM Gateway
- Parses LLM responses for tool calls
- Executes tools and sends results back to LLM
- Provides natural language responses

### Key Concepts

1. **Tools**: Functions that the LLM can call to get information or perform actions
2. **Parameters**: Structured inputs that tools require
3. **Execution**: Running tools and returning results
4. **Integration**: Connecting tools with LLM conversations

## Expected Output

When testing, you should see:

1. **Server startup**: Tools listed and endpoints available
2. **Tool execution**: JSON responses with mock data
3. **LLM integration**: Natural language responses using tool results
4. **Error handling**: Graceful handling of invalid requests

## Troubleshooting

1. **Connection errors**: Make sure virtual environment is activated and dependencies installed
2. **LLM Gateway errors**: Verify `BREX_LLM_GATEWAY_URL` environment variable
3. **Port conflicts**: Change port in `mcp_server.py` if 5000 is in use
4. **Import errors**: Make sure you're running from the correct directory

This implementation demonstrates the basics of MCP - how tools can be exposed and integrated with LLMs for enhanced capabilities.