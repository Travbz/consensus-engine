def format_showdown_response(response_dict):
    """Format the showdown response for proper display."""
    formatted = []
    
    # Extract and format key sections
    for key, value in response_dict.items():
        position = ""
        if "FINAL_POSITION:" in value:
            position = value.split("FINAL_POSITION:")[1]
            if "IMPLEMENTATION:" in position:
                position = position.split("IMPLEMENTATION:")[0]
        elif "IMPLEMENTATION:" in value:
            position = value.split("IMPLEMENTATION:")[1]
            
        position = position.strip()
        formatted.append(f"{key}:\n{position}")
    
    return "\n\n".join(formatted)

def format_discussion_output(result):
    """Format the entire discussion output."""
    if result is None:
        return "[red]No result received from discussion[/red]"
        
    if isinstance(result, str):
        return result
        
    if isinstance(result, dict):
        if "consensus" in result:
            return result["consensus"]
        else:
            return format_showdown_response(result)
            
    return str(result)