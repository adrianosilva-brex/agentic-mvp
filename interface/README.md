# Trip MVP Chat CLI Interface

A chat-like command line interface with interactive provider selection.

## Features

- **Chat Mode**: Type anything without `/` to get an echo response
- **Command Mode**: Use `/` prefix for special commands
- **Interactive Provider Selection**: Navigate with arrow keys to select AI providers

## Available Commands

- `/help` - Display all available commands
- `/providers` - Interactive selection between ANTHROPIC and OPENAI providers
- `exit` or `quit` - Exit the application

## Installation

Install the required dependency:

```bash
pip install blessed
```

Or install from the requirements file:

```bash
pip install -r requirements.txt
```

## Usage

Run the CLI:

```bash
python chat_cli.py
```

Or use the runner script:

```bash
python run_cli.py
```

## Provider Selection

When you run `/providers`:
- Use ↑/↓ arrow keys to navigate
- Press Enter to select a provider
- Press Esc to cancel selection
- The selected provider is shown with an asterisk and highlight
- Current provider is displayed in the prompt

## Examples

```
[ANTHROPIC] > Hello there!
Echo: Hello there!

[ANTHROPIC] > /help
Available Commands:
  /help - List all available configuration commands
  /providers - Select and configure AI providers (ANTHROPIC, OPENAI)

[ANTHROPIC] > /providers
Provider Selection
Use ↑/↓ arrows to navigate, Enter to select, Esc to cancel
→ ANTHROPIC *
  OPENAI

[OPENAI] > This is just a test
Echo: This is just a test
```