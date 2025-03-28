import aiohttp
import logging
import random
import json
import os
import asyncio
import time
from functools import lru_cache
from config import (
    OPENROUTER_API_KEY, 
    OPENROUTER_API_URL, 
    OPENROUTER_MODEL, 
    MAX_TOKENS, 
    TEMPERATURE, 
    ENABLE_CACHING,
    RESPONSE_TIMEOUT,
    CONCURRENT_REQUESTS,
    BOT_NAME,
    BOT_OWNER
)

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.api_url = OPENROUTER_API_URL
        self.model = OPENROUTER_MODEL
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE
        self.enable_caching = ENABLE_CACHING
        self.response_timeout = RESPONSE_TIMEOUT
        
        # Semaphore to limit concurrent API requests
        self.request_semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
        
        # Initialize response cache
        self.response_cache = {}
        self.cache_ttl = 3600  # Cache TTL in seconds (1 hour)
        
        if not self.api_key:
            logger.warning("OpenRouter API key not set! AI chat functionality will not work.")
        
        # Session for API requests
        self.session = None
    
    async def _get_session(self):
        """Get or create an aiohttp ClientSession."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.response_timeout)
            )
        return self.session
    
    def _get_cache_key(self, prompt, user_id=None):
        """Generate a cache key for a given prompt and user."""
        cache_key = f"{prompt}:{user_id if user_id else 'anonymous'}"
        return cache_key
    
    def _check_cache(self, prompt, user_id=None):
        """Check if a response is in the cache and still valid."""
        if not self.enable_caching:
            return None
        
        cache_key = self._get_cache_key(prompt, user_id)
        cached_item = self.response_cache.get(cache_key)
        
        if cached_item:
            timestamp, response = cached_item
            if time.time() - timestamp < self.cache_ttl:
                logger.info(f"Cache hit for prompt: {prompt[:30]}...")
                return response
            else:
                # Remove expired cache entry
                del self.response_cache[cache_key]
        
        return None
    
    def _update_cache(self, prompt, response, user_id=None):
        """Update the cache with a new response."""
        if not self.enable_caching:
            return
        
        cache_key = self._get_cache_key(prompt, user_id)
        self.response_cache[cache_key] = (time.time(), response)
        
        # Clean up old cache entries if cache is getting too large
        if len(self.response_cache) > 100:  # Max 100 cached responses
            oldest_key = min(self.response_cache.keys(), key=lambda k: self.response_cache[k][0])
            del self.response_cache[oldest_key]
    
    async def generate_response(self, prompt, user_id=None):
        """Generate an AI response based on the given prompt."""
        if not self.api_key:
            return "Sorry, the AI service is not configured properly. Please contact the bot administrator."
        
        # Check cache first
        cached_response = self._check_cache(prompt, user_id)
        if cached_response:
            return cached_response
        
        # Enhance the prompt with bot identity information
        enhanced_prompt = f"You are {BOT_NAME}, a Discord bot created by {BOT_OWNER}. Respond to the following message in a helpful and friendly manner: {prompt}"
        
        try:
            # Acquire semaphore to limit concurrent requests
            async with self.request_semaphore:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                data = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": f"You are {BOT_NAME}, a helpful Discord bot created by {BOT_OWNER}. Your responses should be concise and informative."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                }
                
                session = await self._get_session()
                try:
                    async with session.post(
                        self.api_url,
                        headers=headers,
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=self.response_timeout)
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                            
                            # Fallback responses if the API is not available
                            fallback_responses = [
                                "I'm thinking about that...",
                                "That's an interesting question!",
                                "Let me consider that for a moment.",
                                "I'd love to chat about that topic.",
                                "I'm here to help with your questions.",
                                "Thanks for asking. I'm processing that."
                            ]
                            return random.choice(fallback_responses)
                        
                        try:
                            response_data = await response.json()
                            
                            # Parse the response from OpenRouter API
                            if "choices" in response_data and len(response_data["choices"]) > 0:
                                if "message" in response_data["choices"][0] and "content" in response_data["choices"][0]["message"]:
                                    ai_response = response_data["choices"][0]["message"]["content"].strip()
                                    
                                    # Update cache
                                    self._update_cache(prompt, ai_response, user_id)
                                    
                                    return ai_response
                            
                            # If response structure is unexpected
                            logger.warning(f"Unexpected response structure: {response_data}")
                            return "I processed your message, but encountered an unexpected response format."
                        
                        except json.JSONDecodeError:
                            raw_text = await response.text()
                            logger.error(f"Failed to parse JSON response: {raw_text}")
                            return "I received your message, but couldn't process the response correctly."
                
                except asyncio.TimeoutError:
                    logger.error(f"API request timed out after {self.response_timeout} seconds")
                    return "Sorry, it's taking longer than usual to process your request. Please try again in a moment."
        
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "Sorry, I encountered an error while generating a response. Please try again later."
    
    async def is_available(self):
        """Check if the AI service is available."""
        if not self.api_key:
            logger.error("API key is not set, AI service is not available")
            return False
            
        try:
            # Simple test request to check API availability
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5,
            }
            
            logger.info(f"Testing AI service availability with URL: {self.api_url}")
            logger.info(f"Using model: {self.model}")
            
            session = await self._get_session()
            try:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=10)  # Short timeout for status check
                ) as response:
                    status = response.status
                    logger.info(f"AI service test status code: {status}")
                    if status != 200:
                        error_text = await response.text()
                        logger.error(f"AI service test error: {error_text}")
                    return status == 200
            
            except asyncio.TimeoutError:
                logger.error("AI service availability check timed out")
                return False
                
        except Exception as e:
            logger.error(f"Error checking AI service availability: {e}")
            return False
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
