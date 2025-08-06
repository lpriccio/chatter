import gradio as gr
import requests
import json

def get_ollama_models():
    """Get list of available Ollama models"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [model["name"] for model in models]
        return []
    except:
        return []

def chat_with_ollama(message, history, model_name):
    """Send message to Ollama and get response"""
    if not model_name.strip():
        return history + [("You", message), ("Bot", "Please select a model first.")]
    
    try:
        # Format conversation history for Ollama
        messages = []
        for user_msg, bot_msg in history:
            messages.append({"role": "user", "content": user_msg})
            if bot_msg:
                messages.append({"role": "assistant", "content": bot_msg})
        messages.append({"role": "user", "content": message})
        
        # Send request to Ollama
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model_name,
                "messages": messages,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            bot_response = response.json().get("message", {}).get("content", "Sorry, I couldn't generate a response.")
        else:
            bot_response = f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        bot_response = f"Connection error: {str(e)}"
    
    # Update history
    new_history = history + [("You", message), ("Bot", bot_response)]
    return new_history

def create_interface():
    """Create the Gradio chatbot interface"""
    
    # Custom CSS for sky blue text on black background
    css = """
    .gradio-container {
        background-color: black !important;
        color: #87CEEB !important;
    }
    .chatbot .message {
        background-color: #1a1a1a !important;
        border: 1px solid #333 !important;
        color: #87CEEB !important;
    }
    .chatbot .message.user {
        background-color: #2a2a2a !important;
    }
    .chatbot .message.bot {
        background-color: #1a1a1a !important;
    }
    input, textarea, select {
        background-color: #2a2a2a !important;
        color: #87CEEB !important;
        border: 1px solid #555 !important;
    }
    input:focus, textarea:focus, select:focus {
        border-color: #87CEEB !important;
    }
    .gr-button {
        background-color: #2a2a2a !important;
        color: #87CEEB !important;
        border: 1px solid #555 !important;
    }
    .gr-button:hover {
        background-color: #3a3a3a !important;
        border-color: #87CEEB !important;
    }
    .gr-panel {
        background-color: #1a1a1a !important;
        border: 1px solid #333 !important;
    }
    """
    
    with gr.Blocks(css=css, title="Ollama Chatbot") as interface:
        gr.Markdown("# Ollama Chatbot", elem_classes="header")
        
        with gr.Row():
            with gr.Column(scale=1):
                model_input = gr.Textbox(
                    label="Model Name",
                    placeholder="Enter Ollama model name (e.g., llama2, codellama, etc.)",
                    value="",
                    lines=1
                )
                
                available_models = get_ollama_models()
                if available_models:
                    gr.Markdown("**Available Models:**")
                    for model in available_models:
                        gr.Markdown(f"• {model}")
            
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    value=[],
                    height=500,
                    label="Chat History",
                    show_label=True
                )
                
                msg_input = gr.Textbox(
                    label="Your Message",
                    placeholder="Type your message here and press Enter...",
                    lines=2,
                    max_lines=5
                )
                
                with gr.Row():
                    send_btn = gr.Button("Send", variant="primary")
                    clear_btn = gr.Button("Clear Chat", variant="secondary")
        
        # Event handlers
        def submit_message(message, history, model):
            if message.strip():
                new_history = chat_with_ollama(message, history, model)
                return new_history, ""
            return history, message
        
        def clear_chat():
            return []
        
        # Wire up the interface
        msg_input.submit(
            submit_message,
            inputs=[msg_input, chatbot, model_input],
            outputs=[chatbot, msg_input]
        )
        
        send_btn.click(
            submit_message,
            inputs=[msg_input, chatbot, model_input],
            outputs=[chatbot, msg_input]
        )
        
        clear_btn.click(
            clear_chat,
            outputs=[chatbot]
        )
    
    return interface

if __name__ == "__main__":
    app = create_interface()
    app.launch(server_name="127.0.0.1", server_port=7861, share=False)