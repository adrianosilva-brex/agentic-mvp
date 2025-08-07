# Curl commands for testing

## API Keys
### Create a new API key
```
curl -X POST http://localhost:8080/api-keys \
-H "Content-Type: application/json" \
-d '{
  "name": "test_key"
}'
```

### Update an existing API key
```
curl -X PATCH http://localhost:8080/api-keys/apk_abc \
-H "Content-Type: application/json" \
-d '{
  "name": "test_key_2"
}'
```

### View all keys
```
curl -X GET http://localhost:8080/api-keys 
```

### Add rate limit for an API key
```
curl -X POST http://localhost:8080/api-keys/apk_cm6v1kfv2000044ub509k9pqg/rate-limits \
-H "Content-Type: application/json" \
-d '{
  "provider": "OpenAI",
  "model_set": "gpt-4",
  "rpm": 15,
  "tpm": 50000
}'
```

### Update rate limit
```
curl -X PATCH http://localhost:8080/api-keys/apk_cm6v1kfv2000044ub509k9pqg/rate-limits/rl_cm6v1l6su000144ub43ej3rqy \
-H "Content-Type: application/json" \
-d '{  
  "tpm": 100000,
  "rpm": 20
}'
```

### Delete rate limit
```
curl -X DELETE http://localhost:8080/api-keys/apk_cm6v1kfv2000044ub509k9pqg/rate-limits/rl_cm6v1l6su000144ub43ej3rqy
```

### List rate limits of an API key
```
curl -X GET http://localhost:8080/api-keys/apk_cm2zdvo720001cfubhzs2bsuu/rate-limits
```

## Gateway - OpenAI

### List models (GET)
```
curl -X GET http://localhost:8080/gateway/openai/v1/models \
-H "Authorization: Bearer llm_gateway_token_abc"
```

### Embedding
```
curl -X POST http://localhost:8080/gateway/openai/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer llm_gateway_token_abc" \
  -d '{
    "input": "Your text string goes here",
    "model": "text-embedding-3-small"
  }'
```

### Chat completion without streaming
```
curl -X POST  http://localhost:8080/gateway/openai/v1/chat/completions \
-H "Content-Type: application/json" \
-H "Authorization: Bearer llm_gateway_token_abc" \
-H "x-skip-generative-ai-check: true" \
-d '{
  "model": "gpt-4",
  "messages": [{"role": "user", "content": "Hello"}]
}'
```

### Chat completion with streaming
```
curl -X POST http://localhost:8080/gateway/openai/v1/chat/completions \
-H "Content-Type: application/json" \
-H "Authorization: Bearer llm_gateway_token_abc" \
-d '{
  "model": "gpt-4",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": true
}'
```

### Responses without streaming
```
curl -X POST  http://localhost:8080/gateway/openai/v1/responses \
-H "Content-Type: application/json" \
-H "Authorization: Bearer llm_gateway_token_abc" \
-H "x-skip-generative-ai-check: true" \
-d '{
  "model": "gpt-4o",
  "input": "Write a one-sentence bedtime story about a unicorn."
}'
```

### Threads
```
curl -X POST "http://localhost:8080/gateway/openai/v1/threads" \
  -H "Content-Type: application/json" \
```
```
curl -X POST "http://localhost:8080/gateway/openai/v1/threads/{{thread_id}}/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "content": "Hello, how can you help me today?"
  }'
```

## Gateway - Anthropic

### List models (GET)
```
curl -X GET http://localhost:8080/gateway/anthropic/v1/models \
-H "Authorization: Bearer llm_gateway_token_abc"
```

### Message without streaming
```
curl -X POST http://localhost:8080/gateway/anthropic/v1/messages \
-H "Content-Type: application/json" \
-H "x-api-key: llm_gateway_token_abc" \
-H "x-skip-generative-ai-check: true" \
-d '{
  "model": "claude-3-7-sonnet-20250219",
  "system": "You are a helpful assistant.",
  "messages": [{"role": "user", "content": "Hello"}],
  "max_tokens": 2014,
  "stream": false
}'
```

### Message with streaming
```
curl -X POST http://localhost:8080/gateway/anthropic/v1/messages \
-H "Content-Type: application/json" \
-H "x-api-key: llm_gateway_token_abc" \
-H "X-customer-account-id: cuacc_1" \
-H "X-customer-user-id: cuuser_1" \
-d '{
  "model": "claude-3-5-sonnet-20241022",
  "system": "You are a helpful assistant.",
  "messages": [{"role": "user", "content": "Hello"}],
  "max_tokens": 2014,
  "stream": true
}'
```

## Gateway - Gemini

### List models
```
curl "http://localhost:8080/gateway/gemini/v1beta/models" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer llm_gateway_token_abc" \
  -X GET
```

### Generate Content
```
curl "http://localhost:8080/gateway/gemini/v1beta/models/gemini-2.0-flash:generateContent" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer llm_gateway_token_abc" \
  -X POST \
  -d '{
    "contents": [
      {
        "parts": [
          {
            "text": "Explain how AI works in a few words"
          }
        ]
      }
    ]
  }'
```

### Generate Content with streaming
```
curl "http://localhost:8080/gateway/gemini/v1beta/models/gemini-2.0-flash:streamGenerateContent?alt=sse" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer llm_gateway_token_abc" \
  -X POST \
  -d '{
    "contents": [
      {
        "parts": [
          {
            "text": "Explain how AI works in a few words"
          }
        ]
      }
    ]
  }'
```



## Gateway - Generate

### Invoke a published prompt
```
curl -X POST http://localhost:8080/generate/invoke-prompt \
  -H "Content-Type: application/json" \
  -H "X-customer-account-id: cuacc_1" \
-H "X-customer-user-id: cuuser_1" \
  -d '{
    "prompt_name": "weather_bot_prompt",
   "payload": {
    "location": "Shanghai"
  }
}'
```

## Prompts
### Create a new prompt
```
curl -X POST http://localhost:8080/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Prompt",
    "description": "This is an example prompt.",
    "metadata": {
      "process_customer_data": true,
      "enable_evaluation": false
    }
  }'
```

### Soft delete a prompt
```
curl -X DELETE http://localhost:8080/prompts/prompt_cm6f82n850000kwubhjrj5me0 \
  -H "Content-Type: application/json" 
```

### Create a new prompt version
```
curl -X POST http://localhost:8080/prompts/prompt_cm3eyr9ae00000dub3rw1d05l/version \
  -H "Content-Type: application/json" \
  -d '{
  "templated_messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant that can check the weather of a location."
    },
    {
      "role": "user",
      "content": "What is the weather in {{location}}?"
    }
  ],
  "name":"New version",
  "tools": [
    {
      "name": "get_current_weather",
      "description": "Get the current weather",
      "type": "function",
      "scope": "global",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "The city and state, e.g. San Francisco, CA"
          },
          "format": {
            "type": "string",
            "enum": ["celsius", "fahrenheit"],
            "description": "The temperature unit to use. Infer this from the users location."
          }
        },
        "required": ["location", "format"]
      }
    }
  ],
  "tool_choice": {
    "tool_name": "get_current_weather"
  }
}'
```

### Create a new prompt LLM config
```
curl -X POST http://localhost:8080/prompts/prompt_cm3eyr9ae00000dub3rw1d05l/llm-config \
  -H "Content-Type: application/json" \
  -d '{
   "provider":"OpenAI",
   "config":{
      "model":"gpt-4o"
   }
}'
```



### Create a new prompt test payload
```
curl -X POST http://localhost:8080/prompts/prompt_cm7286yk500009aub8kee9jm5/test-payload \
  -H "Content-Type: application/json" \
  -d '{
   "title":"Test payload 1",
   "payload":{
    "location": "Beijing"
  }
}'
```

### Update an existing test payload
```
curl -X PATCH http://localhost:8080/prompts/prompt_cm35df6g10000vqub30f39cvk/test-payload/ptp_cm363ek8j0000otubagq5beub \
  -H "Content-Type: application/json" \
  -d '{
   "title":"Test payload 2"
}'
```

```
curl -X PATCH http://localhost:8080/prompts/prompt_cm35df6g10000vqub30f39cvk/test-payload/ptp_cm363ek8j0000otubagq5beub \
  -H "Content-Type: application/json" \
  -d '{
   "payload":{
    "location": "Shanghai"
  }
}'
```


### Test a prompt on the fly
```
curl --location 'http://localhost:8080/prompts/test' \
--header 'Content-Type: application/json' \
--data '{
    "llm_config": {
        "provider": "OpenAI",
        "config": {
            "model": "gpt-4o"
        }
    },
    "templated_messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant that provides weather information in JSON format."
        },
        {
            "role": "user",
            "content": "What is the current weather in {{ location }} ?"
        }
    ],
    "tools": [
        {
            "type": "function",
            "scope": "parent_prompt_only",
            "name": "get_weather",
            "description": "Get current temperature for a given location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and country e.g. Bogotá, Colombia"
                    }
                },
                "required": [
                    "location"
                ],
                "additionalProperties": false
            },
            "strict": true,
            "current_view": "view"
        }
    ],
    "tool_choice": {
        "tool_name": "get_weather"
    },
    "test_payload": {
        "title": "test",
        "payload": {
            "location": "Austin"
        }
    }
}'
```


### Create a llm config
```
curl -X POST http://localhost:8080/prompts/prompt_cm7286yk500009aub8kee9jm5/llm-config \
  -H "Content-Type: application/json" \
  -d '{
   "provider":"OpenAI",
   "config":{
      "model":"gpt-4o"
   }
}'
```

### Publish a prompt with a version id and llm configs
```
curl -X PATCH http://localhost:8080/prompts/prompt_cm3eyr9ae00000dub3rw1d05l/publish \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_version_id": "prtv_cm3qbop4m00001bubgc8vgv2s",
    "llm_routing_configs": [
      {
        "llm_config_id": "pllmc_cm3t1vye300007yubgdgwdr7o",
        "weight": 100
      }
    ]
  }'
```






### Test a prompt version
```
curl -X POST http://localhost:8080/prompts/test-prompt-version \
  -H "Content-Type: application/json" \
  -d '{
    "promptVersionId": "prtv_cm3qbop4m00001bubgc8vgv2s",
    "promptLLMConfigId": "pllmc_cm3t1vye300007yubgdgwdr7o",
   "payload": {
    "location": "Shanghai"
  }
}'
```


### Test a prompt with batch test payloads
```
curl -X POST http://localhost:8080/prompts/prompt_cm7286yk500009aub8kee9jm5/batch-test \
  -H "Content-Type: application/json" \
  -d '{
    "version_id": "prtv_cm7288o3b00019aubb73ncb3j",
    "llm_config_id": "pllmc_cm728jx1q00001sub0l4991vo",
    "test_payload_ids": ["ptp_cm83m0m7n00007nubawoacz9g", "ptp_cm83m17kn00017nub63am065k"]
}'
```

### Test prompt feedback (submit and update)
```
# Submit initial feedback
curl -X POST http://localhost:8080/feedback/prompt \
  -H "Content-Type: application/json" \
  -H "X-Skip-Genai-Check: true" \
  -d '{
    "vote": "up",
    "prompt_call_records_id": "pcr_test1",
    "expected_response": "Initial expected response"
  }'

# Update feedback
curl -X POST http://localhost:8080/feedback/prompt \
  -H "Content-Type: application/json" \
  -H "X-Skip-Genai-Check: true" \
  -d '{
    "vote": "down",
    "prompt_call_records_id": "pcr_test1",
    "expected_response": "Updated expected response"
  }'

# Verify in database
PGPASSWORD=mysecretpassword psql --host=localhost --port=5678 --dbname=veyond_dev --username=postgres -c "SELECT * FROM prompt_feedback;" | cat
```

### Test chat feedback (submit and update)
```
# Submit initial feedback
curl -X POST http://localhost:8080/feedback/chat \
  -H "Content-Type: application/json" \
  -H "X-Skip-Genai-Check: true" \
  -d '{
    "vote": "up",
    "threadMessageId": "tm_test1",
    "userComment": "Initial feedback"
  }'

# Update feedback
curl -X POST http://localhost:8080/feedback/chat \
  -H "Content-Type: application/json" \
  -H "X-Skip-Genai-Check: true" \
  -d '{
    "vote": "down",
    "threadMessageId": "tm_test1",
    "userComment": "Updated feedback"
  }'

# Verify in database
PGPASSWORD=mysecretpassword psql --host=localhost --port=5678 --dbname=veyond_dev --username=postgres -c "SELECT * FROM chat_feedback;" | cat
```

### Get batch test results
```
curl -X GET http://localhost:8080/prompts/prompt_cm7286yk500009aub8kee9jm5/batches/OpenAI/batch_67e5a397daa48190ab9adc9fb0d55dc2 \
  -H "Content-Type: application/json" 
```

### Render a template on the fly
```
curl -X POST http://localhost:8080/prompts/render \
  -H "Content-Type: application/json" \
  -d '{
   "template": "{{#with expenseInfo}}Use your knowledge about the merchant to infer the meal type. For example, if the merchant is a coffee shop, {{#if (eq merchantCategoryName \"Restaurants\")}} include 'Coffee' in the memo. {{/if}}{{/with}}",
   "payload": {
    "expenseInfo": {
      "merchantCategoryName": "Restaurants"
    }
  }
}'
```

### Get versions of a prompt
```
curl -X GET http://localhost:8080/prompts/prompt_cm3eyr9ae00000dub3rw1d05l/versions \
  -H "Content-Type: application/json"
```

### Get LLM configs of a prompt
```
curl -X GET http://localhost:8080/prompts/prompt_cm3eyr9ae00000dub3rw1d05l/llm-configs \
  -H "Content-Type: application/json"
```


### Get Call records of a prompt
```
curl -X GET http://localhost:8080/prompts/prompt_cm3eyr9ae00000dub3rw1d05l/call-records \
  -H "Content-Type: application/json"
```


### Create a new tool
```
curl -X POST http://localhost:8080/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Tool",
    "description": "This is a test tool",
    "parameters": {
      "type": "object",
      "properties": {
        "name": { "type": "string" }
      },
      "required": ["name"]
    },
    "visibility": "public",
    "strict": true,
    "type": "function"
  }'
```

### List tools
```
curl -X GET http://localhost:8080/tools?visibility=public
```


## Knowledge Base 

### Retrieve
#### AWS
```
curl -X POST http://localhost:8080/knowledge-base/aws/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to request a reimbursement on Brex?", 
    "params": {
      "knowledge_base_id": "KV4VDLTY79",
      "retrieval_configuration": {
        "vectorSearchConfiguration": {
          "numberOfResults": 2
        }
      }
    }
  }'
```
#### Onyx
```
curl -X POST http://localhost:8080/knowledge-base/onyx/retrieve \
  -H "Content-Type: application/json" \
  -d '{    
    "query": "Does Ramp offer bill pay?",
    "params": {
      "assistant_id": "7"
    }
  }'
```

### Retrieve and Generate
#### AWS
```
curl -X POST http://localhost:8080/knowledge-base/aws/retrieve-and-generate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to request a reimbursement on Brex?", 
    "params": {
      "knowledge_base_id": "KV4VDLTY79",
      "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
      "generation_prompt": "How to request a reimbursement on Brex?",
      "orchestration_prompt": "test"
    }
  }'
```
#### Onyx
```
curl -X POST http://localhost:8080/knowledge-base/onyx/retrieve-and-generate \
  -H "Content-Type: application/json" \
  -d '{    
    "query": "Why are customers/prospects ultimately choosing Brex vs Ramp?",
    "params": {
      "assistant_id": "7",
      "prompt_override": {
        "system_prompt": "You are a Sales team assistant for the Brex team to help answer questions on  \"Why Brex is better than its competitors?\". The main competitors is Ramp. You will be provived with documentations on Brex and its competitors product features. You will provide a Sales reprensentative the reasons why Brex is better *only* based on the documentation provided to you. If you do not have the resources to answer a specific question, just respond with \"I do not know\".",
        "task_prompt": "Always respond with a table in the following format: \n- Columns for Brex, Ramp, X, Y, \n- Rows for each requested feature or question and columns\n- Append as the first column \"What are Brex`s differentiators\" which summarizes Brex`s key capabilities for the related feature/question"
      }
    }
  }'
```

### List knowledge bases
#### AWS

```
curl -X GET http://localhost:8080/knowledge-base/aws/list
```
#### Onyx

```
curl -X GET http://localhost:8080/knowledge-base/onyx/list
```

## MCP Servers

### Create a new MCP server
```
curl -X POST http://localhost:8080/mcp-servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test MCP Server",
    "url": "https://api.mcp.com",
    "authentication_secret_key": "secret_key"
  }'
```

### List tools of a MCP server
```
curl -X GET http://localhost:8080/mcp-servers/mcp_server_cmar2gb840000gtubc9l9emkb/tools
```