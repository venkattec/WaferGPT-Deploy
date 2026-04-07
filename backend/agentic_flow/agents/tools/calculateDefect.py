import cv2
import numpy as np
from agents.tools.describeDefect import describe_defect_percentage
# from describeDefect import describe_defect_percentage,no_defect

import uuid,os
def detect_defects(npy_path=None, image_path=None, threshold=200, min_area=500, size=(520, 520)):
    """
    Detect defects from a `.npy` file or an image file, calculate defect percentages, and show details.

    Parameters:
    - npy_path: Path to the `.npy` file (default is None).
    - image_path: Path to the image file (default is None).
    - threshold: Threshold value for binarization (default is 200).
    - min_area: Minimum area to consider a region as a defect (default is 100 pixels).
    - size: Tuple specifying the target size (width, height) to resize the input (default is (520, 520)).

    Returns:
    - defect_percentage: Percentage of the wafer that is defected.
    - largest_bbox_location: Location of the bounding box with the largest area (e.g., "top", "bottom", etc.).
    """

    # Check if npy_path is provided
    if npy_path:
        # Load the .npy file
        wafer_map = np.load(npy_path)

        # Normalize the wafer map if needed
        wafer_map = np.uint8(255 * (wafer_map - np.min(wafer_map)) / (np.max(wafer_map) - np.min(wafer_map)))
        wafer_map_resized = cv2.resize(wafer_map, size, interpolation=cv2.INTER_LINEAR)
    elif image_path:
        # Load the image
        wafer_map_resized = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        wafer_map_resized = cv2.resize(wafer_map_resized, size, interpolation=cv2.INTER_LINEAR)
    else:
        raise ValueError("Both 'npy_path' and 'image_path' cannot be None. Please provide one.")

    # Apply thresholding to isolate defects
    _, binary = cv2.threshold(wafer_map_resized, threshold, 255, cv2.THRESH_BINARY)

    # Find contours of the defect regions
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Create a 3-channel image for visualization
    output_image = cv2.cvtColor(wafer_map_resized, cv2.COLOR_GRAY2BGR)

    # Total defect area
    total_defect_area = 0
    defect_areas = []
    largest_area = 0
    largest_bbox = None

    # Process contours to calculate defect areas and draw bounding boxes
    for contour in contours:
        # Calculate the area of the defect
        area = cv2.contourArea(contour)

        # Process only if the area is larger than the minimum area
        if area >= min_area:
            total_defect_area += area
            defect_areas.append(area)

            # Get bounding box coordinates
            x, y, w, h = cv2.boundingRect(contour)

            # Update the largest defect area and bounding box
            if area > largest_area:
                largest_area = area
                largest_bbox = (x, y, w, h)

            # Draw bounding box
            cv2.rectangle(output_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(output_image, f"Area: {area}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    # Calculate total wafer area (circular region)
    wafer_mask = np.zeros_like(binary, dtype=np.uint8)
    center = (size[0] // 2, size[1] // 2)
    radius = min(size) // 2
    cv2.circle(wafer_mask, center, radius, 255, -1)
    total_wafer_area = np.sum(wafer_mask == 255)

    # Calculate defect percentage
    defect_percentage = (total_defect_area / total_wafer_area) * 100

    # Save the output image
    output_path = "output/output_per.png"
    unique_filename = f"processed_{uuid.uuid4().hex}.png"
    output_path = os.path.join("/app/processed_image", unique_filename)
    cv2.imwrite(output_path, output_image)

    # Display results
    print(f"Defect Areas: {defect_areas}")
    print(f"Total Defect Area: {total_defect_area}")
    print(f"Total Wafer Area: {total_wafer_area}")
    print(f"Defect Percentage: {defect_percentage:.2f}%")
    print(f"Output image saved as {output_path}")

    return describe_defect_percentage(defect_percentage), output_path

if __name__ == "__main__":
    # Example usage
    npy_path = "D:/WaferGPT-Deploy/backend/npy_files/image1.npy"  # Replace with the path to your `.npy` file
    img_path = "D:/WaferGPT-Deploy/backend/png_files/image1.png"  # Replace with the path to your image file
    print(detect_defects(image_path=img_path, threshold=200, min_area=500))  # Adjust `min_area` as needed

    # img_path = "output_image.png"
    # print(detect_defects(image_path=img_path))