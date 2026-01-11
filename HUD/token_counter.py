"""
Token Counter Utility for LUDO
Provides token estimation and context management for efficient API usage
"""

def estimate_tokens(text):
    """
    Estimate the number of tokens in a text string.
    Uses approximation: 1 token ≈ 4 characters for English text.
    
    Args:
        text (str): The text to estimate tokens for
        
    Returns:
        int: Estimated number of tokens
    """
    if not text:
        return 0
    
    # Basic approximation: 1 token ≈ 4 characters
    # This is a rough estimate but works well for English text
    char_count = len(text)
    token_estimate = char_count / 4
    
    # Round up to be conservative
    return int(token_estimate) + 1


def estimate_conversation_tokens(conversation_history):
    """
    Estimate total tokens in a conversation history.
    
    Args:
        conversation_history (list): List of conversation strings
        
    Returns:
        int: Total estimated tokens
    """
    total_tokens = 0
    for message in conversation_history:
        total_tokens += estimate_tokens(message)
    return total_tokens


def trim_to_token_budget(conversation_history, max_tokens=2000):
    """
    Trim conversation history to fit within token budget.
    Keeps most recent messages and removes oldest ones.
    
    Args:
        conversation_history (list): List of conversation strings
        max_tokens (int): Maximum token budget
        
    Returns:
        list: Trimmed conversation history
    """
    if not conversation_history:
        return []
    
    # Start from the end (most recent) and work backwards
    trimmed = []
    current_tokens = 0
    
    for message in reversed(conversation_history):
        message_tokens = estimate_tokens(message)
        
        if current_tokens + message_tokens <= max_tokens:
            trimmed.insert(0, message)
            current_tokens += message_tokens
        else:
            # Budget exceeded, stop adding older messages
            break
    
    return trimmed


def create_conversation_summary(conversation_history, max_length=500):
    """
    Create a condensed summary of conversation history.
    Extracts key topics and facts from older conversations.
    
    Args:
        conversation_history (list): List of conversation strings
        max_length (int): Maximum character length for summary
        
    Returns:
        str: Condensed summary of conversations
    """
    if not conversation_history:
        return ""
    
    # Extract user queries and key responses
    key_points = []
    
    for i, message in enumerate(conversation_history):
        if message.startswith("User: "):
            # Extract user query
            query = message.replace("User: ", "").strip()
            if len(query) > 10:  # Only meaningful queries
                key_points.append(f"Q: {query}")
        elif message.startswith("LUDO: ") and i > 0:
            # Extract first sentence of response as key point
            response = message.replace("LUDO: ", "").strip()
            first_sentence = response.split('.')[0] + '.'
            if len(first_sentence) < 150:  # Keep it concise
                key_points.append(f"A: {first_sentence}")
    
    # Combine into summary
    summary = " | ".join(key_points)
    
    # Trim to max length if needed
    if len(summary) > max_length:
        summary = summary[:max_length] + "..."
    
    return summary


def get_context_stats(conversation_history):
    """
    Get statistics about the current context.
    
    Args:
        conversation_history (list): List of conversation strings
        
    Returns:
        dict: Statistics including token count, message count, etc.
    """
    total_tokens = estimate_conversation_tokens(conversation_history)
    message_count = len(conversation_history)
    user_messages = sum(1 for msg in conversation_history if msg.startswith("User: "))
    
    total_chars = sum(len(msg) for msg in conversation_history)
    
    return {
        'total_tokens': total_tokens,
        'message_count': message_count,
        'user_messages': user_messages,
        'total_characters': total_chars,
        'avg_tokens_per_message': total_tokens // message_count if message_count > 0 else 0
    }


if __name__ == "__main__":
    # Test the token counter
    test_text = "Hello, this is a test message for token counting."
    tokens = estimate_tokens(test_text)
    print(f"Text: '{test_text}'")
    print(f"Estimated tokens: {tokens}")
    print(f"Characters: {len(test_text)}")
    print(f"Ratio: {len(test_text) / tokens:.2f} chars/token")
