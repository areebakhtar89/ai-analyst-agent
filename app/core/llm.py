"""LLM configuration and management for the AI Analyst Agent.

This module provides a centralized interface for accessing the language model
used throughout the application for natural language processing tasks.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()


def get_llm():
    """Get configured LLM instance for AI operations.
    
    Returns a pre-configured ChatGoogleGenerativeAI instance with
    optimized settings for data analysis tasks.
    
    Returns:
        ChatGoogleGenerativeAI: Configured LLM instance
    """
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2  # Low temperature for consistent, analytical responses
    )
