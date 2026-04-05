import gradio as gr
import time,os
from getResponse import invoke_api
# from test_flask import invoke_api
# Function to get all image paths dynamically
def load_images_from_folder(folder_path, extensions=(".png", ".jpg", ".jpeg")):
    return [
        os.path.join(folder_path, file)
        for file in sorted(os.listdir(folder_path))
        if file.lower().endswith(extensions)
    ]


# Load images dynamically from the 'images' folder
image_folder = "png_files"  # Change this to your folder path
preset_images = load_images_from_folder(image_folder)


# Function to handle like/dislike
def print_like_dislike(x: gr.LikeData):
    print(x.index, x.value, x.liked)


def clear_message():
    time.sleep(3)
    return ""


def submit_feedback(feedback):
    print(f"User Feedback: {feedback}")  # Print in backend
    return "✅ Thank you for your feedback! 🎉", ""


# Function to handle user message & image, maintaining session history
# Function to handle user message & image, maintaining session history
# Function to handle user message & image, maintaining session history
def add_message(history, message, selected_image):
    if history is None:
        history = []  # Initialize session history

    # Append image properly using Markdown if selected
    if selected_image:
        # image_markdown = f"![Wafer Image]({selected_image})"
        history.append({"role": "user", "content": {"path": selected_image}})  # Show image in chat

    # Append user message
    if message:
        history.append({"role": "user", "content": message})

    return history, ""  # Return updated history and clear input box
# Bot response function (simulating typing effect)


# def bot(history):
#
#     # response = str(time.time())
#     response = {
#         "message": "Hello, how can I help you today?",
#         "image_path": "https://gradio-static-files.s3.us-west-2.amazonaws.com/lion.jpg",
#     }
#     if "image_path" in response:
#         # analyzed_image_path = random.choice(preset_images)  # Pick a random analyzed image
#         history.append({"role": "assistant", "content": response['message']})  # Show text
#         history.append({"role": "assistant", "content": {"path": response['image_path']}})  # Show image
#     else:
#         history.append({"role": "assistant", "content": response['message']})  # Show text
#     # history.append({"role": "assistant", "content": response})
#     yield history


def bot(history, session_image):
    """Handles bot response, processes selected image and user question"""

    if not history or len(history) < 2:
        history.append({"role": "assistant", "content": "Please select an image and ask a question."})
        yield history
        return

    # Extract last user message
    user_message = None
    for entry in reversed(history):
        if entry["role"] == "user" and isinstance(entry["content"], str):
            user_message = entry["content"]
            break

    if not user_message:
        history.append({"role": "assistant", "content": "I didn't receive a question. Please try again."})
        yield history
        return

    # Process the selected image and user question
    response = invoke_api(session_image, user_message)
    if "image_path" in response:
        # analyzed_image_path = random.choice(preset_images)  # Pick a random analyzed image
        history.append({"role": "assistant", "content": response['result']})  # Show text
        history.append({"role": "assistant", "content": {"path": response['image_path']}})  # Show image
    else:
        history.append({"role": "assistant", "content": response['result']})  # Show text
    # history.append({"role": "assistant", "content": response})
    yield history


# Function to store selected image per user session
def get_selected_image(evt: gr.SelectData, session_image):
    session_image = preset_images[evt.index]  # Update selected image for the session
    return session_image

js_func = """
function refresh() {
    const url = new URL(window.location);

    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""
# js=js_func
with gr.Blocks(theme='CultriX/gradio-theme',
               css="textarea:focus {background-color: rgb(250,242,233) !important; }") as demo:
    with gr.Row():
        with gr.Column(scale=1):
            img = gr.Image(
                "logo.jpg", height=160, width=160, show_label=False, show_download_button=False,
                show_fullscreen_button=False)
        with gr.Column(scale=4):
            gr.Markdown("""<h1 style='font-size: 40px; text-align: left; padding-top: 20px'> Welcome to Wafer-Defect-Detector 🔍 </h1>
                <h2 style='font-size: 20px; text-align: left;'>WaferGPT is a specialized AI-driven tool designed to analyze semiconductor wafers for defects.</h2>
                Pick a wafer image and interact with our AI assistant to detect issues and gain insights on the type
                of defect, location of the defect, defect percentage and much more.
                """)
    #########################################################################3

    # with gr.Row():
    #
    #     with gr.Column(variant="panel",scale=1):
    #         # gr.Markdown("## ðŸ›  How to Use")
    #         with gr.Row():
    #             gr.Text(
    #                 label="ðŸ›  How to Use",
    #                 value=
    #                 "ðŸ”¹Step 1: Select the file from the Pick a wafer to examineðŸ–¼ï¸\n\n"
    #                 "ðŸ”¹Step 2: Ask your question in the chatbox ðŸ¤–\n\n"
    #                 "ðŸ”¹Step 3: View the AI's analysis and the processed image. ðŸ“Š\n\n"
    #                 "ðŸ”¹Step 4: Please give your Valuable Feedback ðŸ“",
    #                 interactive=False
    #             )
    #
    #     with gr.Column(variant="panel",scale=1):
    #         # gr.Markdown("## Demo Video")
    #         gr.Video("https://gradio-static-files.s3.us-west-2.amazonaws.com/world.mp4",height=200,width=420,label="Demo Video")
    #
    #     with gr.Column(variant="panel", scale=1):
    #         feedback_box = gr.Textbox(
    #             label="Feedback ðŸ“",
    #             info="Please provide your feedback here",
    #             placeholder="Type your feedback here...",
    #             lines=3
    #         )
    #         submit_btn = gr.Button("Submit Feedback", variant="huggingface", size="sm")
    #
    #         # Output message
    #         thanks_message = gr.Markdown("")
    #
    #         # Button action
    #         submit_btn.click(submit_feedback, feedback_box, [thanks_message, feedback_box])
    with gr.Sidebar(open=False):
        with gr.Column(variant="panel"):
            gr.Text(
                label="🛠 How to Use",
                value=(
                    "1: Select a wafer image 🖼️\n\n"
                    "2: Ask your question in the chatbox 🤖\n\n"
                    "3: View the AI's analysis and the processed image 📊\n\n"
                    "4: Provide feedback 📝"
                ),
                interactive=False
            )

        # with gr.Column(variant="panel"):
        #     gr.Video("https://gradio-static-files.s3.us-west-2.amazonaws.com/world.mp4", height=200, width="auto",
        #              label="Demo Video")

        with gr.Column(variant="panel"):
            feedback_box = gr.Textbox(
                label="Feedback 📝",
                info="Please provide your feedback here",
                placeholder="Type your feedback here...",
                lines=3
            )
            submit_btn = gr.Button("Submit Feedback", variant="huggingface", size="sm")
            thanks_message = gr.Markdown("")
            submit_btn.click(submit_feedback, feedback_box, [thanks_message, feedback_box])

            ###############################################################################
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(elem_id="WaferGPT", bubble_full_width=False, type="messages", label="WaferGPT")
            chat_input = gr.Textbox(placeholder="Enter your Question...", interactive=True, show_label=False,
                                    )

        with gr.Column(scale=1):
            session_history = gr.State([])  # Store chat history per session
            session_image = gr.State(None)  # Store selected image per session

            image_display = gr.Gallery(preset_images, label="Pick a Wafer", interactive=False, columns=3,
                                       show_download_button=False, height="auto")
            image_display.select(get_selected_image, [session_image], session_image)

    # When user submits a message, add text & image to chatbot (session-aware)
    chat_msg = chat_input.submit(
        add_message, [chatbot, chat_input, session_image], [chatbot, chat_input]
    )

    # Bot responds to user's message
    bot_msg = chat_msg.then(bot, [chatbot, session_image], chatbot, api_name="bot_response")

    bot_msg.then(lambda: gr.Textbox(interactive=True), None, [chat_input])

    # Handle likes/dislikes
    chatbot.like(print_like_dislike, None, None, like_user_message=False)

# Launch app
demo.queue().launch(server_name='0.0.0.0',server_port=8501)
