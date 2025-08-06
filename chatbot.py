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
        return history + [(message, "Please select a model first.")]
    
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
    new_history = history + [(message, bot_response)]
    return new_history

def create_interface():
    """Create the Gradio chatbot interface"""
    
    # Custom CSS for sky blue text on black background
    css = """
    /* Overall app background */
    body, .gradio-container, .app, .main {
        background-color: #000000 !important;
        color: #87CEEB !important;
    }
    
    /* Main content area */
    .contain {
        background-color: #000000 !important;
    }
    
    /* Chatbot component styling */
    .chatbot {
        background-color: #000000 !important;
        border: 1px solid #333 !important;
    }
    
    /* Chat messages */
    .chatbot .message {
        background-color: #1a1a1a !important;
        border: 1px solid #333 !important;
        color: #87CEEB !important;
    }
    
    .chatbot .message.user {
        background-color: #2a2a2a !important;
        color: #87CEEB !important;
    }
    
    .chatbot .message.bot {
        background-color: #1a1a1a !important;
        color: #87CEEB !important;
    }
    
    /* Input fields */
    input, textarea, .textbox input, .textbox textarea {
        background-color: #2a2a2a !important;
        color: #87CEEB !important;
        border: 1px solid #555 !important;
    }
    
    input:focus, textarea:focus, .textbox input:focus, .textbox textarea:focus {
        border-color: #87CEEB !important;
        outline: none !important;
        box-shadow: 0 0 0 1px #87CEEB !important;
    }
    
    /* Buttons */
    .btn, button, .gr-button {
        background-color: #2a2a2a !important;
        color: #87CEEB !important;
        border: 1px solid #555 !important;
    }
    
    .btn:hover, button:hover, .gr-button:hover {
        background-color: #3a3a3a !important;
        border-color: #87CEEB !important;
    }
    
    .btn-primary {
        background-color: #2a2a2a !important;
        border-color: #87CEEB !important;
    }
    
    /* Labels and text */
    label, .gr-form label, .label-wrap, .output-markdown {
        color: #87CEEB !important;
    }
    
    /* Panels and containers */
    .panel, .gr-panel, .form {
        background-color: #1a1a1a !important;
        border: 1px solid #333 !important;
    }
    
    /* Markdown content */
    .prose, .markdown {
        color: #87CEEB !important;
    }
    
    /* Override any white backgrounds */
    * {
        scrollbar-color: #555 #000 !important;
    }
    
    ::-webkit-scrollbar {
        background-color: #000 !important;
    }
    
    ::-webkit-scrollbar-thumb {
        background-color: #555 !important;
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
        def add_user_message(message, history):
            if message.strip():
                return history + [(message, "")], ""
            return history, message
        
        def get_bot_response(history, model):
            if history and history[-1][1] == "":  # Last message has empty bot response
                user_message = history[-1][0]
                # Remove the temporary message and get proper response
                history_without_last = history[:-1]
                new_history = chat_with_ollama(user_message, history_without_last, model)
                return new_history
            return history
        
        def clear_chat():
            return []
        
        # Wire up the interface with chained events
        msg_submit = msg_input.submit(
            add_user_message,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input]
        ).then(
            get_bot_response,
            inputs=[chatbot, model_input],
            outputs=[chatbot]
        )
        
        send_click = send_btn.click(
            add_user_message,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input]
        ).then(
            get_bot_response,
            inputs=[chatbot, model_input],
            outputs=[chatbot]
        )
        
        clear_btn.click(
            clear_chat,
            outputs=[chatbot]
        )
    
    return interface

if __name__ == "__main__":
    app = create_interface()
    app.launch(server_name="127.0.0.1", server_port=7861, share=False)