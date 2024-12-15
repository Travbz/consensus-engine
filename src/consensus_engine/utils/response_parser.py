"""Utilities for parsing LLM responses."""
from typing import Dict, Any, Optional
import re

class ResponseParser:
    @staticmethod
    def parse_structured_response(response: str) -> Dict[str, Any]:
        """Parse a structured response into components."""
        components = {}
        current_section = None
        current_content = []
        
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