import cv2
import numpy as np
from describeDefect import describe_defect_location,no_defect
import uuid,os
def detect_and_localize_defects(npy_path=None, image_path=None, threshold=200, min_area=1000, size=(520, 520)):
    """
    Detect and localize defects from a `.npy` file or an image file, resized to a standard size.

    Parameters:
    - npy_path: Path to the `.npy` file (default is None).
    - image_path: Path to the image file (default is None).
    - threshold: Threshold value for binarization (default is 200).
    - min_area: Minimum area to consider a region as a defect (default is 100 pixels).
    - size: Tuple specifying the target size (width, height) to resize the input (default is (520, 520)).

    Returns:
    - largest_defect_location: A string indicating the location of the largest defect.
    """

    # Check if npy_path is provided
    if npy_path:
        # Load the .npy file
        wafer_map = np.load(npy_path)

        # Normalize the wafer map if needed (e.g., if it's not in range [0, 255])
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

    largest_defect_area = 0
    largest_defect_bounding_box = None
    largest_defect_location = ""

    # To calculate the average location of defects
    total_x = 0
    total_y = 0
    total_defects = 0

    print("Detected Large Defects:")
    for i, contour in enumerate(contours):
        # Calculate the area of the defect
        area = cv2.contourArea(contour)

        # Process only if the area is larger than the minimum area
        if area >= min_area:
            # Calculate bounding box around the defect
            x, y, w, h = cv2.boundingRect(contour)

            # Calculate centroid of the defect region
            cx, cy = x + w // 2, y + h // 2

            # Draw the bounding box and centroid on the output image
            cv2.rectangle(output_image, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Green box
            cv2.circle(output_image, (cx, cy), 5, (0, 0, 255), -1)  # Red centroid

            # Print defect details
            print(
                f"Defect {i + 1}: Area={area}, Bounding Box [x={x}, y={y}, w={w}, h={h}], Centroid [cx={cx}, cy={cy}]")

            # Update largest defect if the current one is larger
            if area > largest_defect_area:
                largest_defect_area = area
                largest_defect_bounding_box = (x, y, w, h)

            # Track the centroids for average location calculation
            total_x += cx
            total_y += cy
            total_defects += 1

    if total_defects > 0:
        # Compute average centroid position for defect location classification
        avg_cx = total_x // total_defects
        avg_cy = total_y // total_defects

        # Determine the location of the defects based on average centroid position
        image_width, image_height = wafer_map_resized.shape[1], wafer_map_resized.shape[0]

        location = []

        # Top or Bottom
        if avg_cy < image_height / 3:
            location.append("Top")
        elif avg_cy + h > 2 * image_height / 3:
            location.append("Bottom")
        else:
            location.append("Middle")

        # Left or Right
        if avg_cx < image_width / 3:
            location.append("Left")
        elif avg_cx + w > 2 * image_width / 3:
            location.append("Right")
        else:
            location.append("Middle")

        largest_defect_location = ", ".join(location)
        # Save the output image with defects highlighted
        output_path = "output/output_loc.png"
        unique_filename = f"processed_{uuid.uuid4().hex}.png"
        output_path = os.path.join("/home/sbna/Documents/WaferGPT-Frontend/processed_image", unique_filename)
        cv2.imwrite(output_path, output_image)
        print(f"Output image saved as {output_path}")

        return describe_defect_location(location[0], location[1]), output_path
    else:
        unique_filename = f"processed_{uuid.uuid4().hex}.png"
        output_path = os.path.join("/home/sbna/Documents/WaferGPT-Frontend/processed_image", unique_filename)
        cv2.imwrite(output_path, output_image)
        return describe_defect_location("", ""), output_path


if __name__ == "__main__":

    # # Example usage
    npy_path = "npy_files/image3.npy"  # Replace with the path to your `.npy` file
    print(detect_and_localize_defects(npy_path, threshold=200, min_area=500))  # Adjust `min_area` as needed

    # Using an image file
    # image_path = "output_image.png"
    # defect_location = detect_and_localize_defects(image_path=image_path)