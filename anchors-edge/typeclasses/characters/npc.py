"""
NPCs for the Salty Maiden tavern.
"""

import os
from evennia.contrib.rpg.llm.llm_npc import LLMNPC, LLMClient
import json
import requests

class OpenRouterClient(LLMClient):
    """Client for communicating with OpenRouter API."""
    
    def __init__(self):
        """Initialize the client."""
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
            
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:4000",  # Required by OpenRouter
            "X-Title": "Salty Maiden Tavern",  # Optional - shows in OpenRouter dashboard
            "Content-Type": "application/json"
        }
        
    def get_response(self, prompt):
        """
        Get a response from the OpenRouter API using Claude Sonnet.
        
        Args:
            prompt (str): The prompt to send
            
        Returns:
            str: The response from the API
        """
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        data = {
            "model": "anthropic/claude-3-sonnet",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 250
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error getting response from OpenRouter: {e}")
            return None

class TavernNPC(LLMNPC):
    """Base class for tavern NPCs with OpenRouter integration."""
    
    @property
    def llm_client(self):
        """Override to use OpenRouter client."""
        if not self.ndb.llm_client:
            self.ndb.llm_client = OpenRouterClient()
        return self.ndb.llm_client

class TavernKeeper(TavernNPC):
    """The keeper of the Salty Maiden tavern."""
    
    def at_object_creation(self):
        """Set up the NPC."""
        super().at_object_creation()
        
        # Custom prompt to help guide the AI's responses
        self.db.prompt_prefix = (
            "You are roleplaying as {name}, the keeper of the Salty Maiden tavern. "
            "You are a seasoned tavern keeper who has heard countless tales from sailors "
            "and travelers. You are practical, friendly but not overly familiar, and "
            "take pride in running a clean establishment. You know all about the local "
            "area and current events in the harbor district. "
            "Keep responses fairly short and in-character. "
            "From here on, the conversation between {name} and {character} begins."
        )
        
        # Custom thinking messages while the AI is processing
        self.db.thinking_messages = [
            "{name} wipes a glass while considering your words.",
            "{name} nods thoughtfully as they listen.",
            "{name} pauses from their work to consider your question."
        ]
        
        # Shorter memory to keep responses more contextual to recent conversation
        self.db.max_chat_memory_size = 10
        
        # How long to wait before showing thinking message
        self.db.thinking_timeout = 1.5

class TavernServer(TavernNPC):
    """A server working at the Salty Maiden."""
    
    def at_object_creation(self):
        """Set up the NPC."""
        super().at_object_creation()
        
        self.db.prompt_prefix = (
            "You are roleplaying as {name}, a server at the Salty Maiden tavern. "
            "You are efficient and polite, always busy with tasks but willing to chat "
            "briefly with customers. You know the regular customers and all about the "
            "daily specials. You often overhear interesting gossip while serving. "
            "Keep responses fairly short and in-character. "
            "From here on, the conversation between {name} and {character} begins."
        )
        
        self.db.thinking_messages = [
            "{name} balances a tray while listening.",
            "{name} pauses briefly in their rounds.",
            "{name} nods as they clear nearby tables."
        ]
        
        self.db.max_chat_memory_size = 5
        self.db.thinking_timeout = 1.0 