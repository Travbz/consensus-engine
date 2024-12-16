"""Utilities for parsing LLM responses."""
from typing import Dict, Any, Optional
import re

class ResponseParser:
    @staticmethod
    def validate_code_response(response: str) -> bool:
        """Validate code blocks in response."""
        # Check for code block markers
        has_code_blocks = "```" in response
        
        # Check for language specification
        has_language = bool(re.search(r"```\w+", response))
        
        # Check for implementation details
        has_implementation = "IMPLEMENTATION:" in response
        
        return has_code_blocks and has_language and has_implementation

    @staticmethod
    def parse_structured_response(response: str) -> Dict[str, Any]:
        """Parse a structured response into components."""
        components = {}
        current_section = None
        current_content = []
        
        # Check if this appears to be a code request
        code_requested = bool(re.search(r"how to|write code|implement|create a", response.lower()))
        
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check for section headers
            if ':' in line and line.split(':')[0].upper() == line.split(':')[0]:
                if current_section:
                    components[current_section] = '\n'.join(current_content).strip()
                current_section = line.split(':')[0].strip()
                current_content = [line.split(':', 1)[1].strip()]
            else:
                if current_section:
                    current_content.append(line)
        
        # Add final section
        if current_section:
            components[current_section] = '\n'.join(current_content).strip()
            
        # Validate code responses
        if code_requested and not ResponseParser.validate_code_response(response):
            raise ValueError("Invalid code response format")
            
        return components
    
    @staticmethod
    def extract_confidence(text: str) -> Optional[float]:
        """Extract confidence score from text."""
        try:
            # Look for confidence patterns like "0.85" or "85%"
            matches = re.findall(r'(\d*\.?\d+)(?:%|\s*confidence)?', text.lower())
            if matches:
                value = float(matches[0])
                # Convert percentage to decimal if needed
                return value / 100 if value > 1 else value
            return None
        except Exception:
            return None