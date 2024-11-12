import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict, Any

# Load environment variables and configure API
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Custom styles
def apply_custom_styles():
    st.markdown("""
        <style>
        .stButton button {
            width: 100%;
            border-radius: 5px;
            margin: 2px;
        }
        .story-text {
            background-color: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }
        </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize or reset session state variables"""
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "game_state" not in st.session_state:
        st.session_state.game_state = {
            "health": 100,
            "inventory": [],
            "choices_made": 0
        }

def create_model() -> genai.GenerativeModel:
    """Create and configure the Gemini model"""
    generation_config = {
        "temperature": 0.8,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1024,
        "response_mime_type": "text/plain",
    }
    
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config
    )

def generate_story_response(conversation_history: List[Dict[str, Any]]) -> str:
    """Generate the next part of the story using the Gemini model"""
    try:
        model = create_model()
        chat_session = model.start_chat(history=conversation_history)
        
        # Add context about game state to the prompt
        context = f"""
        Current game state:
        - Health: {st.session_state.game_state['health']}
        - Inventory: {', '.join(st.session_state.game_state['inventory']) if st.session_state.game_state['inventory'] else 'empty'}
        - Choices made: {st.session_state.game_state['choices_made']}
        
        Please continue the story and provide 2-3 clear choices for the player.
        Incorporate the player's health and inventory into the narrative when relevant.
        """
        
        # Get response from model
        response = chat_session.send_message(
            conversation_history[-1]["parts"][0]["text"] + "\n" + context
        )
        
        return response.text
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return "Something went wrong in the forest... Please try again."

def update_game_state(response_text: str):
    """Update game state based on the story response"""
    # Dangerous actions that reduce health
    dangerous_actions = ['fight', 'confront', 'explore', 'approach', 'follow', 'ignore warning', 'trap', 'venture deeper']
    for action in dangerous_actions:
        if action in response_text.lower():
            st.session_state.game_state['health'] -= 15  # Deduct more health for dangerous actions
    
    # Inventory items and their effects
    inventory_items = {
        'potion': {'effect': 'restore_health', 'value': 20},
        'sword': {'effect': 'attack_bonus', 'value': 5},
        'key': {'effect': 'unlock', 'value': 1},
        'map': {'effect': 'navigation_help', 'value': 1},
        'shield': {'effect': 'reduce_damage', 'value': 10},
        'amulet': {'effect': 'protection', 'value': 5}
    }
    
    # Add items to inventory if found
    for item in inventory_items.keys():
        if f"found a {item}" in response_text.lower() and item not in st.session_state.game_state['inventory']:
            st.session_state.game_state['inventory'].append(item)
    
    # Increment choices counter
    st.session_state.game_state['choices_made'] += 1

def use_inventory_item(item_name):
    """Use an item from the inventory if applicable"""
    if item_name == "potion" and "potion" in st.session_state.game_state['inventory']:
        # Potion restores health
        st.session_state.game_state['health'] = min(100, st.session_state.game_state['health'] + 20)
        st.session_state.game_state['inventory'].remove("potion")
        st.success("You used a potion and regained 20 health!")
    elif item_name == "shield" and "shield" in st.session_state.game_state['inventory']:
        # Shield reduces health loss in next dangerous action
        st.session_state.game_state['inventory'].remove("shield")
        st.success("You equipped a shield. It will reduce damage from the next danger you encounter.")
    else:
        st.warning(f"You cannot use {item_name} now.")

def display_game_state():
    """Display the current game state in the sidebar"""
    st.sidebar.header("Game Status")
    
    # Health bar
    st.sidebar.progress(st.session_state.game_state['health'] / 100)
    st.sidebar.write(f"Health: {st.session_state.game_state['health']}%")
    
    # Inventory
    st.sidebar.subheader("Inventory")
    if st.session_state.game_state['inventory']:
        for item in st.session_state.game_state['inventory']:
            if st.sidebar.button(f"Use {item.capitalize()}"):
                use_inventory_item(item)
            st.sidebar.write(f"- {item}")
    else:
        st.sidebar.write("Empty")
    
    # Choices made
    st.sidebar.write(f"Choices made: {st.session_state.game_state['choices_made']}")

def main():
    st.set_page_config(page_title="The Cursed Forest", layout="wide")
    apply_custom_styles()
    
    st.title("🌲 The Cursed Forest - Interactive Adventure")
    
    # Initialize session state
    initialize_session_state()
    
    # Add restart button in sidebar
    if st.sidebar.button("Restart Game"):
        st.session_state.clear()
        st.rerun()
    
    # Introduction message if starting new game
    if not st.session_state.conversation_history:
        intro_message = {
            "role": "model",
            "parts": [{
                "text": (
                    "Welcome, brave soul! You are Kaelen, a wanderer who finds yourself lost in the mysterious Cursed Forest. "
                    "Strange creatures, hidden dangers, and an ancient curse lurk in the shadows. Legend has it that the heart "
                    "of the forest holds a powerful artifact, but no one who has ventured deep enough has ever returned.\n\n"
                    "Your adventure begins at the edge of the forest, where an eerie fog hangs in the air. You notice:\n\n"
                    "1. A narrow path leading deeper into the woods\n"
                    "2. A strange glowing mushroom near a hollow tree\n"
                    "3. The sound of running water in the distance\n\n"
                    "What would you like to do?"
                )}]
        }
        st.session_state.conversation_history.append(intro_message)
        st.session_state.messages.append(intro_message)
    
    # Display game state in sidebar
    display_game_state()
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message("assistant" if message["role"] == "model" else "user"):
            st.markdown(message["parts"][0]["text"])
    
    # Game over check
    if st.session_state.game_state['health'] <= 0:
        st.error("💀 Game Over - You have perished in the Cursed Forest")
        if st.button("Start New Game"):
            st.session_state.clear()
            st.rerun()
        return
    
    # User input
    user_input = st.chat_input("What will you do next?", key="user_input")
    
    if user_input:
        # Add user input to history
        user_message = {"role": "user", "parts": [{"text": user_input}]}
        st.session_state.conversation_history.append(user_message)
        st.session_state.messages.append(user_message)
        
        with st.spinner("The forest whispers..."):
            # Generate and display response
            response = generate_story_response(st.session_state.conversation_history)
            
            # Update game state based on response
            update_game_state(response)
            
            # Add response to history
            ai_message = {"role": "model", "parts": [{"text": response}]}
            st.session_state.conversation_history.append(ai_message)
            st.session_state.messages.append(ai_message)
        
        # Force a rerun to update the display
        st.rerun()

if __name__ == "__main__":
    main()
