#!/usr/bin/env python3
import sys
from typing import List, Optional

try:
    from blessed import Terminal
except ImportError:
    print("Error: 'blessed' library is required. Install it with: pip install blessed")
    sys.exit(1)

from utils.llm_gateway_interface import fetch_models, LLMModel, send_message
import sys
import os
# Add server path for TMC imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import TMC components
from server.base_tmc_provider import TMCProviderType
from server.tmc_provider_factory import TMCRouter



class ChatCLI:
    def __init__(self):
        self.term = Terminal()
        self.stream = False
        self.providers = ["anthropic", "openai"]
        self.selected_provider = self.providers[0]
        self.tmcs = ["deck", "anon", "supergood.ai"]
        self.selected_tmc = self.tmcs[0]
        
        # Initialize TMC router
        self.tmc_router = TMCRouter()
        
        # Initialize models list - will be populated when fetched
        self.models: List[LLMModel] = []
        self.selected_model = "No model selected"
        self.selected_model_id = None
        
        # Load models for the initial provider  
        self.refresh_models()
        
        self.commands = {
            "/help": "List all available configuration commands",
            "/providers": "Select and configure AI providers",
            "/models": "Select and configure AI models",
            "/stream": "Toggle response streaming mode",
            "/tmc": "See the selected third party TMC data provider",
            "/tmcs": "Select and configure third party TMC data providers",
            "/model": "See the selected model",
            "/sync": "Show embedded URL for the selected TMC provider"
        }
    
    def refresh_models(self):
        """Fetch models for the currently selected provider."""
        try:
            print(f"{self.term.dim}Fetching models for {self.selected_provider}...{self.term.normal}")
            self.models = fetch_models(self.selected_provider)
            if self.models:
                # Select the first model by default
                self.selected_model = self.models[0].model_name
                self.selected_model_id = self.models[0].model_id
            else:
                self.selected_model = "No models available"
                self.selected_model_id = None
        except Exception as e:
            print(f"{self.term.red}Error fetching models: {e}{self.term.normal}")
            self.models = []
            self.selected_model = "Error loading models"
            self.selected_model_id = None
        
    def print_welcome(self):
        """Print welcome message and instructions."""
        print(f"{self.term.bold_green}Welcome to Trip MVP Chat CLI{self.term.normal}")
        print(f"{self.term.cyan}Type commands starting with / or just chat normally{self.term.normal}")
        print(f"{self.term.dim}Type /help for available commands{self.term.normal}")
        print("-" * 50)

    def handle_selection(self, title: str, items: List, current_item, 
                        display_formatter=None, on_selection=None):
        """
        Generic selection handler for interactive lists.
        
        Args:
            title: Title to display (e.g., "Provider Selection")
            items: List of items to select from
            current_item: Currently selected item
            display_formatter: Function to format item display (item) -> str
            on_selection: Function called when selection changes (old_item, new_item) -> None
        
        Returns:
            Selected item or None if cancelled
        """
        if not items:
            print(f"{self.term.red}No items available{self.term.normal}")
            return None
            
        print(f"\n{self.term.bold_yellow}{title}{self.term.normal}")
        print(f"{self.term.dim}Use ↑/↓ arrows to navigate, Enter to select, Esc to cancel{self.term.normal}")
        
        # Find current item index
        current_index = 0
        for i, item in enumerate(items):
            if item == current_item:
                current_index = i
                break
        
        # Default display formatter
        if display_formatter is None:
            display_formatter = lambda item: str(item)
        
        # Print initial list
        for i, item in enumerate(items):
            display_text = display_formatter(item)
            if i == current_index:
                print(f"→ {display_text} *")
            else:
                print(f"  {display_text}")
        
        with self.term.cbreak(), self.term.hidden_cursor():
            while True:
                # Get user input
                key = self.term.inkey()
                
                if key.code == self.term.KEY_UP:
                    current_index = (current_index - 1) % len(items)
                elif key.code == self.term.KEY_DOWN:
                    current_index = (current_index + 1) % len(items)
                elif key.code == self.term.KEY_ENTER:
                    selected_item = items[current_index]
                    # Clear the list lines
                    for _ in range(len(items)):
                        print(f"\r{self.term.clear_eol}{self.term.move_up}", end='')
                    
                    if selected_item != current_item:
                        print(f"\r{self.term.clear_eol}{self.term.green}✓ Selected: {display_formatter(selected_item)}{self.term.normal}")
                        if on_selection:
                            on_selection(current_item, selected_item)
                        print()
                    else:
                        print(f"\r{self.term.clear_eol}{self.term.yellow}Selection unchanged{self.term.normal}\n")
                    
                    return selected_item
                elif key.code == self.term.KEY_ESCAPE:
                    # Clear the list lines
                    for _ in range(len(items)):
                        print(f"\r{self.term.clear_eol}{self.term.move_up}", end='')
                    print(f"\r{self.term.clear_eol}{self.term.yellow}Selection cancelled{self.term.normal}\n")
                    return None
                
                # Redraw the list if arrow key was pressed
                if key.code in (self.term.KEY_UP, self.term.KEY_DOWN):
                    # Move cursor up to redraw the list
                    for _ in range(len(items)):
                        print(f"\r{self.term.move_up}", end='')
                    
                    # Redraw each line
                    for i, item in enumerate(items):
                        print(f"\r{self.term.clear_eol}", end='')
                        display_text = display_formatter(item)
                        if i == current_index:
                            print(f"→ {display_text} *")
                        else:
                            print(f"  {display_text}")

    def handle_help_command(self):
        """Display help with all available commands."""
        print(f"\n{self.term.bold_yellow}Available Commands:{self.term.normal}")
        for cmd, description in self.commands.items():
            print(f"  {self.term.green}{cmd}{self.term.normal} - {description}")
        print()

    def handle_models_command(self):
        """Interactive model selection interface."""
        if not self.models:
            print(f"{self.term.red}No models available{self.term.normal}")
            return
            
        print(f"\n{self.term.bold_yellow}Model Selection for {self.selected_provider}{self.term.normal}")
        print(f"{self.term.dim}Use ↑/↓ arrows to navigate, Enter to select, Esc to cancel{self.term.normal}")
        
        # Find current model index by name
        current_index = 0
        for i, model in enumerate(self.models):
            if model.model_name == self.selected_model:
                current_index = i
                break
        
        # Print initial model list
        for i, model in enumerate(self.models):
            modalities = "+".join(model.input_modalities)
            inference = "+".join(model.inference_types)
            if i == current_index:
                print(f"→ {model.model_name} [{modalities}] ({inference}) *")
            else:
                print(f"  {model.model_name} [{modalities}] ({inference})")
        
        with self.term.cbreak(), self.term.hidden_cursor():
            while True:
                # Get user input
                key = self.term.inkey()
                
                if key.code == self.term.KEY_UP:
                    current_index = (current_index - 1) % len(self.models)
                elif key.code == self.term.KEY_DOWN:
                    current_index = (current_index + 1) % len(self.models)
                elif key.code == self.term.KEY_ENTER:
                    selected_model_obj = self.models[current_index]
                    self.selected_model = selected_model_obj.model_name
                    self.selected_model_id = selected_model_obj.model_id
                    
                    # Clear the model list lines
                    for _ in range(len(self.models)):
                        print(f"\r{self.term.clear_eol}{self.term.move_up}", end='')
                    print(f"\r{self.term.clear_eol}{self.term.green}✓ Selected model: {self.selected_model}{self.term.normal}\n")
                    break
                elif key.code == self.term.KEY_ESCAPE:
                    # Clear the model list lines
                    for _ in range(len(self.models)):
                        print(f"\r{self.term.clear_eol}{self.term.move_up}", end='')
                    print(f"\r{self.term.clear_eol}{self.term.yellow}Selection cancelled{self.term.normal}\n")
                    break
                
                # Redraw the model list if arrow key was pressed
                if key.code in (self.term.KEY_UP, self.term.KEY_DOWN):
                    # Move cursor up to redraw the list
                    for _ in range(len(self.models)):
                        print(f"\r{self.term.move_up}", end='')
                    
                    # Redraw each model line
                    for i, model in enumerate(self.models):
                        print(f"\r{self.term.clear_eol}", end='')
                        modalities = "+".join(model.input_modalities)
                        inference = "+".join(model.inference_types)
                        if i == current_index:
                            print(f"→ {model.model_name} [{modalities}] ({inference}) *")
                        else:
                            print(f"  {model.model_name} [{modalities}] ({inference})")

    def handle_stream_command(self):
        print(f"\n{self.term.bold_yellow}Changing reponse streaming mode{self.term.normal}")
        if (self.stream):
            self.stream = False
            print(f"{self.term.green}Response streaming mode disabled{self.term.normal}")
        else:
            self.stream = True
            print(f"{self.term.green}Response streaming mode enabled{self.term.normal}")
        
    def handle_tmc_command(self):
        """Sync the trip data with the third party provider."""
        def on_tmc_selection(old_tmc, new_tmc):
            self.selected_tmc = new_tmc
            print(f"{self.term.green}Selected TMC: {new_tmc}{self.term.normal}")
        
        selected = self.handle_selection(
            title="Third Party Provider Selection",
            items=self.tmcs,
            current_item=self.selected_tmc,
            on_selection=on_tmc_selection
        )

    def handle_sync_command(self):
        """Show embedded URL for the selected TMC provider."""
        try:
            # Map UI TMC names to provider types
            tmc_mapping = {
                "deck": TMCProviderType.DECK,
                "anon": TMCProviderType.ANON,
                "supergood.ai": TMCProviderType.SUPERGOOD
            }
            
            provider_type = tmc_mapping.get(self.selected_tmc)
            if not provider_type:
                print(f"{self.term.red}Unknown TMC provider: {self.selected_tmc}{self.term.normal}")
                return
            
            print(f"{self.term.bold_yellow}Generating embedded URL for {self.selected_tmc}...{self.term.normal}")
            
            # Generate a sample user ID for demo purposes
            user_id = "demo_user_123"
            
            # Get embedded URL from the TMC router
            embedded_url = self.tmc_router.get_embedded_url(
                user_id=user_id, 
                provider_type=provider_type,
                source_provider=None
            )
            
            print(f"\n{self.term.bold_green}✓ Embedded URL Generated{self.term.normal}")
            print(f"{self.term.cyan}Provider:{self.term.normal} {self.selected_tmc}")
            print(f"{self.term.cyan}User ID:{self.term.normal} {user_id}")
            print(f"{self.term.cyan}URL:{self.term.normal} {embedded_url}")
            
            # Show provider-specific information
            if self.selected_tmc == "anon":
                print(f"{self.term.dim}This URL opens the Anon migration modal for transferring bookings from Navan{self.term.normal}")
            elif self.selected_tmc == "deck":
                print(f"{self.term.dim}This URL opens the Deck travel management interface{self.term.normal}")
            elif self.selected_tmc == "supergood.ai":
                print(f"{self.term.dim}This URL opens the Supergood.ai analytics and optimization dashboard{self.term.normal}")
            
            print()
            
        except Exception as e:
            print(f"{self.term.red}Error generating embedded URL: {str(e)}{self.term.normal}")
            print(f"{self.term.dim}Make sure the {self.selected_tmc} provider is properly configured{self.term.normal}")
                            
    def handle_providers_command(self):
        """Interactive provider selection interface."""
        print(f"\n{self.term.bold_yellow}Provider Selection{self.term.normal}")
        print(f"{self.term.dim}Use ↑/↓ arrows to navigate, Enter to select, Esc to cancel{self.term.normal}")
        
        # Find current provider index by name
        current_index = 0
        for i, provider in enumerate(self.providers):
            if provider == self.selected_provider:
                current_index = i
                break
        
        # Print initial provider list
        for i, provider in enumerate(self.providers):
            if i == current_index:
                print(f"→ {provider} *")
            else:
                print(f"  {provider}")
        
        with self.term.cbreak(), self.term.hidden_cursor():
            while True:
                # Get user input
                key = self.term.inkey()
                
                if key.code == self.term.KEY_UP:
                    current_index = (current_index - 1) % len(self.providers)
                elif key.code == self.term.KEY_DOWN:
                    current_index = (current_index + 1) % len(self.providers)
                elif key.code == self.term.KEY_ENTER:
                    new_provider = self.providers[current_index]
                    if new_provider != self.selected_provider:
                        self.selected_provider = new_provider
                        # Clear the provider list lines
                        for _ in range(len(self.providers)):
                            print(f"\r{self.term.clear_eol}{self.term.move_up}", end='')
                        print(f"\r{self.term.clear_eol}{self.term.green}✓ Selected provider: {self.selected_provider}{self.term.normal}")
                        # Refresh models for the new provider
                        self.refresh_models()
                        print()
                    else:
                        # Clear the provider list lines
                        for _ in range(len(self.providers)):
                            print(f"\r{self.term.clear_eol}{self.term.move_up}", end='')
                        print(f"\r{self.term.clear_eol}{self.term.yellow}Provider unchanged{self.term.normal}\n")
                    break
                elif key.code == self.term.KEY_ESCAPE:
                    # Clear the provider list lines
                    for _ in range(len(self.providers)):
                        print(f"\r{self.term.clear_eol}{self.term.move_up}", end='')
                    print(f"\r{self.term.clear_eol}{self.term.yellow}Selection cancelled{self.term.normal}\n")
                    break
                
                # Redraw the provider list if arrow key was pressed
                if key.code in (self.term.KEY_UP, self.term.KEY_DOWN):
                    # Move cursor up to redraw the list
                    for _ in range(len(self.providers)):
                        print(f"\r{self.term.move_up}", end='')
                    
                    # Redraw each provider line
                    for i, provider in enumerate(self.providers):
                        print(f"\r{self.term.clear_eol}", end='')
                        if i == current_index:
                            print(f"→ {provider} *")
                        else:
                            print(f"  {provider}")

    def handle_command(self, command: str):
        """Process slash commands."""
        command = command.strip().lower()
        
        if command == "/help":
            self.handle_help_command()
        elif command == "/providers":
            self.handle_providers_command()
        elif command == "/model":
           print(f"{self.term.green}Selected Model: {self.selected_model}{self.term.normal}")
        elif command == "/models":
            self.handle_models_command()
        elif command == "/stream":
            self.handle_stream_command()
        elif command == "/tmcs":
            self.handle_tmc_command()
        elif command == "/tmc":
            print(f"{self.term.green}Selected TMC: {self.selected_tmc}{self.term.normal}")
        elif command == "/sync":
            self.handle_sync_command()
        else:
            print(f"{self.term.red}Unknown command: {command}{self.term.normal}")
            print(f"{self.term.dim}Type /help for available commands{self.term.normal}")

    def llm_call(self, message: str):
        """Echo non-command messages."""
        json_response = send_message(self.selected_provider, self.selected_model_id, message)
        content = json_response["content"][0]["text"] if self.selected_provider == "anthropic" else json_response["choices"][0]["message"]["content"]
        print(f"{self.term.blue}LLM Response: {self.term.normal}{content}")

    def run(self):
        """Main CLI loop."""
        self.print_welcome()
        
        try:
            while True:
                try:
                    # Show current provider and model in prompt
                    provider_indicator = f"{self.term.dim}[{self.selected_provider}]{self.term.normal}"
                    model_indicator = f"{self.term.dim}[{self.selected_model}]{self.term.normal}" if hasattr(self, 'selected_model') else ""
                    prompt = f"{provider_indicator}{model_indicator} > " if model_indicator else f"{provider_indicator} > "
                    user_input = input(prompt).strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() in ['exit', 'quit', '/exit', '/quit']:
                        print(f"{self.term.green}Goodbye!{self.term.normal}")
                        break
                    
                    if user_input.startswith('/'):
                        self.handle_command(user_input)
                    else:
                        self.llm_call(user_input)
                        
                except KeyboardInterrupt:
                    print(f"\n{self.term.green}Goodbye!{self.term.normal}")
                    break
                    
        except (EOFError, KeyboardInterrupt):
            print(f"\n{self.term.green}Goodbye!{self.term.normal}")


def main():
    """Entry point for the chat CLI."""
    cli = ChatCLI()
    cli.run()


if __name__ == "__main__":
    main()