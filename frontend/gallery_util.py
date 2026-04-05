import glob,os
# Define image directory
image_dir = "png_files"
import gradio as gr

# Function to categorize images
def get_image_categories():
    wafer_images = sorted(glob.glob(os.path.join(image_dir, "image*.png")))
    sem_images = sorted(glob.glob(os.path.join(image_dir, "sem*.png")))
    return wafer_images, sem_images

# Function to show the gallery based on selection
def show_gallery(choice):
    wafer_images, sem_images = get_image_categories()

    if choice == "Wafer Images":
        return gr.update(visible=False), gr.update(visible=True), wafer_images
    elif choice == "SEM Images":
        return gr.update(visible=False), gr.update(visible=True), sem_images
    return gr.update(visible=True), gr.update(visible=False), [], ""

# Function to go back to selection
def go_back():
    return gr.update(visible=True), gr.update(visible=False), []

# Function to store selected image in state
def select_image(evt: gr.SelectData):
    image_path = evt.value["image"]["path"]  # Extract the image path
    filename = os.path.basename(image_path)  # Extract the filename for display
    image_path = os.path.abspath(os.path.join(image_dir,filename))
    return image_path  # Return both values
