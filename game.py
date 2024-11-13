import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Set up Gemini API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Define a function to generate the story response using Gemini
def generate_story_response(conversation_history):
    # Define the generation configuration
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1024,  # Lower token limit for concise responses
        "response_mime_type": "text/plain",
    }

    # Create and configure the model for chat
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash", 
        generation_config=generation_config
    )
    
    # Start or continue the chat session
    chat_session = model.start_chat(history=conversation_history)
    
    # Send the user input and get the response
    response = chat_session.send_message(conversation_history[-1]["parts"][0]["text"])
    
    return response.text

# Main Streamlit app function
def main():
    st.title("The Cursed Forest - Interactive Adventure")

    # Introduction to the story
    intro_message = {
        "role": "model",
        "parts": [
            {
                "text": (
                    "Welcome, brave soul! You are Kaelen, a wanderer who finds himself lost in the mysterious Cursed Forest. "
                    "Strange creatures, hidden dangers, and an ancient curse lurk in the shadows. Legend has it that the heart of the forest holds a powerful artifact, "
                    "but no one who has ventured deep enough has ever returned. It's up to you to decide whether to seek the artifact or escape the forest alive. "
                    "But beware, not all paths lead to safety... "
                    "\n\nYour adventure begins at the edge of the forest, where an eerie fog hangs in the air. Do you wish to enter the forest or turn back to safety?"
                )
            }
        ]
    }

    # Initialize chat history in session state
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = [intro_message]
        st.session_state.messages = [intro_message]

    # Display the chat history
    for message in st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown(message["parts"][0]["text"])

    # Function to handle interaction and generate the next part of the story
    def handle_interaction(user_input):
        # Add user input to conversation history
        user_message = {
            "role": "user",
            "parts": [{"text": user_input}]
        }
        st.session_state.conversation_history.append(user_message)

        # Create a placeholder for the AI response
        response_placeholder = st.empty()

        # Show loading spinner
        with st.spinner("Thinking..."):
            # Generate AI response based on the updated conversation history
            ai_response = generate_story_response(st.session_state.conversation_history)

        # Display the response in the placeholder
        response_placeholder.markdown(ai_response)

        # Add AI response to conversation history
        ai_message = {
            "role": "model",
            "parts": [{"text": ai_response}]
        }
        st.session_state.conversation_history.append(ai_message)
        st.session_state.messages.append(user_message)
        st.session_state.messages.append(ai_message)

    # Accept user input
    user_input = st.chat_input("What will you do next?")

    # When user enters a response, process it
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        handle_interaction(user_input)

        # Check for an end condition in the AI response
        if "The End." in st.session_state.messages[-1]["parts"][0]["text"]:
            st.write("### Game Over")

if __name__ == "__main__":
    main()
