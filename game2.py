import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict, Any

# Load environment variables and configure API
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

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
        .highlight {
            color: #FFA500;
            font-weight: bold;
        }
        .inventory-item {
            color: #FFA500;
            cursor: pointer;
        }
        </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "game_state" not in st.session_state:
        st.session_state.game_state = {
            "health": 100,
            "inventory": [],
            "choices_made": 0,
            "found_item": None
        }

def create_model() -> genai.GenerativeModel:
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
    try:
        model = create_model()
        chat_session = model.start_chat(history=conversation_history)
        context = f"""
        Current game state:
        - Health: {st.session_state.game_state['health']}
        - Inventory: {', '.join(st.session_state.game_state['inventory']) if st.session_state.game_state['inventory'] else 'empty'}
        - Choices made: {st.session_state.game_state['choices_made']}
        
        Please continue the story and provide 2-3 clear choices for the player.
        Highlight items the player finds in the story with ** so they are easy to pick up.
        Easy to find health_potion when health is lower than 30.
        """
        response = chat_session.send_message(
            conversation_history[-1]["parts"][0]["text"] + "\n" + context
        )
        return response.text
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return "Something went wrong in the forest... Please try again."

def update_game_state(response_text: str):
    dangerous_actions = ['fight', 'confront', 'explore', 'approach', 'follow', 'ignore warning', 'trap', 'venture deeper']
    for action in dangerous_actions:
        if action in response_text.lower():
            st.session_state.game_state['health'] -= 15
    st.session_state.game_state['health'] = max(st.session_state.game_state['health'], 0)

    inventory_items = {
        'potion': 'You found a **potion**!',
        'sword': 'You found a **sword**!',
        'key': 'You found a **key**!',
        'map': 'You found a **map**!',
        'shield': 'You found a **shield**!',
        'amulet': 'You found an **amulet**!',
        'health_potion': 'You found a **health potion**!'
    }
    for item, notification in inventory_items.items():
        if f"**{item}**" in response_text.lower():
            st.session_state.game_state['found_item'] = item
            st.session_state.game_state['choices_made'] += 1
            st.write(f"🎉 You found a **{item.capitalize()}**!")

def add_item_to_inventory():
    item = st.session_state.game_state['found_item']
    if item and item not in st.session_state.game_state['inventory']:
        st.session_state.game_state['inventory'].append(item)
        st.session_state.game_state['found_item'] = None
        st.success(f"{item.capitalize()} added to inventory!")

def use_health_potion():
    if 'health_potion' in st.session_state.game_state['inventory']:
        st.session_state.game_state['health'] += 30
        st.session_state.game_state['health'] = min(st.session_state.game_state['health'], 100)
        st.session_state.game_state['inventory'].remove('health_potion')
        st.success("You used a health potion! Health restored by 30 points.")
    else:
        st.error("You don't have any health potions!")

def display_game_state():
    st.sidebar.header("Game Status")
    health_percentage = max(0, st.session_state.game_state['health']) / 100
    st.sidebar.progress(health_percentage)
    st.sidebar.write(f"Health: {max(0, st.session_state.game_state['health'])}%")

    st.sidebar.subheader("Inventory")
    if st.session_state.game_state['inventory']:
        for item in st.session_state.game_state['inventory']:
            if item == 'health_potion':
                st.sidebar.markdown(f"- **{item.capitalize()}** (Use to restore health)", unsafe_allow_html=True)
            else:
                st.sidebar.write(f"- {item.capitalize()}")
    else:
        st.sidebar.write("Empty")

    st.sidebar.write(f"Choices made: {st.session_state.game_state['choices_made']}")

def main():
    st.set_page_config(page_title="The Cursed Forest", layout="wide")
    apply_custom_styles()
    st.title("🌲 The Cursed Forest - Interactive Adventure")
    initialize_session_state()

    if st.sidebar.button("Restart Game"):
        st.session_state.clear()
        st.rerun()

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

    display_game_state()

    for message in st.session_state.messages:
        with st.chat_message("assistant" if message["role"] == "model" else "user"):
            text = message["parts"][0]["text"]
            highlighted_text = text.replace("**", "<span class='highlight'>").replace("**", "</span>")
            st.markdown(highlighted_text, unsafe_allow_html=True)

    if st.session_state.game_state['health'] <= 0:
        st.error("💀 Game Over - You have perished in the Cursed Forest")
        if st.button("Start New Game"):
            st.session_state.clear()
            st.rerun()
        return

    if st.session_state.game_state['found_item']:
        item = st.session_state.game_state['found_item']
        if st.button(f"Pick up {item.capitalize()}"):
            add_item_to_inventory()

    if 'health_potion' in st.session_state.game_state['inventory']:
        if st.button("Use Health Potion"):
            use_health_potion()

    user_input = st.chat_input("What will you do next?", key="user_input")

    if user_input:
        user_message = {"role": "user", "parts": [{"text": user_input}]}
        st.session_state.conversation_history.append(user_message)
        st.session_state.messages.append(user_message)

        # Update choices made when user provides input
        st.session_state.game_state['choices_made'] += 1

        with st.spinner("The forest whispers..."):
            response = generate_story_response(st.session_state.conversation_history)
            update_game_state(response)
            ai_message = {"role": "model", "parts": [{"text": response}]}
            st.session_state.conversation_history.append(ai_message)
            st.session_state.messages.append(ai_message)

        st.rerun()

if __name__ == "__main__":
    main()
