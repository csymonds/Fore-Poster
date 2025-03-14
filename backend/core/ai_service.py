"""
AI Service for Fore-Poster

This module handles all interactions with AI services like OpenAI.
It provides functions for generating content, with potential for
future extensions like web search and image generation.
"""
import os
import logging
import requests
import json

# Initialize logger
logger = logging.getLogger(__name__)

class AIService:
    """Service class for AI-related operations."""
    
    # Default system prompt for AI content generation
    DEFAULT_SYSTEM_PROMPT = "You are a social media expert who writes engaging, factual posts for X (formerly Twitter). Your goal is growing your audience and get attention. Make the algorithm happy. Keep it under 280 characters. Avoid exclamation marks. Don't be cringe. Don't be cheesy. Use emojis"
    
    def __init__(self, api_key=None):
        """
        Initialize the AI service with an API key.
        
        Args:
            api_key: Optional API key. If not provided, will attempt to read from environment.
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.api_url = "https://api.openai.com/v1/responses"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.is_initialized = False
        
        if self.api_key:
            self.is_initialized = True
            logger.info("OpenAI API initialized with Bearer authentication")
        else:
            logger.warning("No OpenAI API key provided or found in environment")
    
    def is_available(self):
        """Check if the AI service is available and configured properly."""
        return self.is_initialized and self.api_key is not None
    
    def generate_post_content(self, prompt, system_prompt=None, temperature=None, web_search=None):
        """
        Generate social media post content using AI.
        
        Args:
            prompt: The prompt to send to the AI service
            system_prompt: Optional override for system instructions
            temperature: Optional override for model temperature
            web_search: Optional override for web search capability
            
        Returns:
            dict: A dictionary with the generated text or error information
        """
        if not self.is_available():
            logger.warning("AI service not available, using fallback response")
            return {
                'success': True,
                'text': 'Banger X post: Breaking news in AI: revolutionary breakthroughs in neural net efficiency have emerged in the research labs of Silicon Valley. Stay tuned for more updates!'
            }
        
        try:
            # Log the request
            logger.info(f"Sending request to OpenAI API with prompt: {prompt}")
            
            # Use provided system prompt or default
            system_instructions = system_prompt or self.DEFAULT_SYSTEM_PROMPT
            
            # System instructions and prompt
            full_prompt = f"{system_instructions}\n\n{prompt}"
            
            # Make a direct API request using HTTP Bearer authentication
            data = {
                "model": "gpt-4o",
                "input": full_prompt
            }
            
            # Add temperature if provided
            if temperature is not None:
                data["temperature"] = float(temperature)
            
            # Add web search tools if enabled
            if web_search or (web_search is None and True):  # Default to True if not specified
                data["tools"] = [{ "type": "web_search_preview" }]
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Response received: {result}")
                
                # Extract the response text based on the structure provided in the example
                output_text = ""
                
                try:
                    # Navigate the response structure to find the text
                    if "output" in result and result["output"]:
                        for message in result["output"]:
                            if "content" in message:
                                for content in message["content"]:
                                    if "text" in content:
                                        output_text = content["text"]
                                        break
                except Exception as e:
                    logger.warning(f"Error extracting text from JSON structure: {e}")
                
                # If we couldn't extract the text using the expected structure, use the raw output
                if not output_text:
                    output_text = str(result)
                    logger.warning(f"Using fallback text extraction: {output_text[:50]}...")
                
                logger.info(f"Successfully extracted text: {output_text[:50]}...")
                
                return {
                    'success': True,
                    'text': output_text
                }
            else:
                error_message = f"API request failed with status code: {response.status_code}, Response: {response.text}"
                logger.error(error_message)
                return {
                    'success': False,
                    'error': error_message
                }
            
        except Exception as e:
            logger.error(f"Error generating content from OpenAI: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_with_web_search(self, query):
        """
        Generate content with web search capability (placeholder for future implementation).
        
        Args:
            query: The search query to use
            
        Returns:
            dict: A dictionary with the generated text or error information
        """
        logger.info("Web search functionality not yet implemented")
        return {
            'success': False,
            'error': 'Web search functionality not yet implemented'
        }
    
    def generate_image(self, prompt):
        """
        Generate image based on prompt (placeholder for future implementation).
        
        Args:
            prompt: The image generation prompt
            
        Returns:
            dict: A dictionary with image information or error
        """
        logger.info("Image generation functionality not yet implemented")
        return {
            'success': False,
            'error': 'Image generation functionality not yet implemented'
        }

# Create a singleton instance for use throughout the application
ai_service = AIService()

def init_ai_service(api_key=None):
    """
    Initialize the AI service with the given API key.
    This function can be called at application startup.
    
    Args:
        api_key: Optional API key to use
        
    Returns:
        The initialized AI service instance
    """
    global ai_service
    ai_service = AIService(api_key)
    return ai_service 