import torch
from transformers import ViTForImageClassification, ViTImageProcessor
from PIL import Image
import requests
import torch.nn.functional as F
from describeDefect import describe_sem_defect_types

# Set device (GPU if available, else CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load the trained model
model_path = "models/vit_model_best_sem_with_non_26_new.pth"  # Change this if using a different saved model
model = ViTForImageClassification.from_pretrained("google/vit-base-patch16-224",num_labels=26,ignore_mismatched_sizes=True)
model.load_state_dict(torch.load(model_path, map_location=device))
model.to(device)
model.eval()

# class_names = ["Break","Bridege","Collapse","Corner_Rounding","Deformed","Gap","Merging","Missing","Overlay_Error","Oversized","Repeating","Sidewall_Roughness","Undersized"]  # Update with your classes
class_names = ['Break', 'Break_non_defect', 'Bridge', 'Bridge_non_defect', 'Collapse', 'Collapse_non_defect', 'Corner_Rounding', 'Corner_Rounding_non_defect', 'Deformed', 'Deformed_non_defect', 'Gap', 'Gap_non_defect', 'Merging', 'Merging_non_defect', 'Missing', 'Missing_non_defect', 'Overlay_Error', 'Overlay_Error_non_defect', 'Oversized', 'Oversized_non_defect', 'Repeating', 'Repeating_non_defect', 'Sidewall_Roughness', 'Sidewall_Roughness_non_defect', 'Undersized', 'Undersized_non_defect']

# Load the image processor (preprocessing)
processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224")

def preprocess_image(image_path):
    """Preprocess an image for ViT model inference."""
    print("received img for sem :",image_path) 
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")  # Convert to tensor
    return inputs["pixel_values"].to(device)

def predict(image_path):
    """Perform inference on a single image."""
    image_tensor = preprocess_image(image_path)

    with torch.no_grad():
        outputs = model(pixel_values=image_tensor)
        logits = outputs.logits
        probs = F.softmax(logits, dim=-1)
        predicted_class_idx = logits.argmax(-1).item()  # Get predicted class index
        confidence = probs[0, predicted_class_idx].item()
    predicted_class = class_names[predicted_class_idx] if class_names else predicted_class_idx
    print(f"Predicted Class: {predicted_class}")
    print("confidence ",confidence)
    if "non_defect" in predicted_class:
        predicted_class = "No Defect"
    return describe_sem_defect_types(predicted_class)

if __name__ == "__main__":
    # Example usage
    image_path = "/home/sbna/Documents/SEM/dataset/val/Repeating/repeating_defect_100.png"
    predict(image_path)

