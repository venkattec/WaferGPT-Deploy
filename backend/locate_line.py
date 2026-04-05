import cv2,os,uuid
import numpy as np
from describeDefect import describe_defect_location


def locate_sem_line_defect(defect_path):
    # Load images
    ideal_path = "/home/sbna/Documents/WaferGPT-Backend/png_files/sem4.png"  # Ideal wafer image

    ideal = cv2.imread(ideal_path, cv2.IMREAD_GRAYSCALE)
    defect = cv2.imread(defect_path, cv2.IMREAD_GRAYSCALE)

    # Ensure same size
    if ideal.shape != defect.shape:
        defect = cv2.resize(defect, (ideal.shape[1], ideal.shape[0]))

    # Compute absolute difference
    diff = cv2.absdiff(ideal, defect)

    # Threshold to highlight differences
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

    # Remove noise using morphological operations
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

    # Find contours (defects only)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Get image dimensions
    h, w = defect.shape
    max_area = 0
    # Determine defect locations
    detected_regions = []
    for contour in contours:
        x, y, w_c, h_c = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        # print(area)
        if area > max_area and area > 20:
            cx, cy = x + w_c // 2, y + h_c // 2  # Center of defect
            # cv2.rectangle(defect, (x, y), (x + w_c, y + h_c), (0, 255, 0), 2)  # Green box
            if cy < h /3:
                detected_regions.append("Top")
            elif cy + h_c >2 * h / 3:
                detected_regions.append("Bottom")
            else:
                detected_regions.append("Middle")
            if cx < w /3:
                detected_regions.append("Left")
            elif cx + w_c >2 * w / 3:
                detected_regions.append("Right")
            else:
                detected_regions.append("Center")

    # Print detected defect locations
    output = cv2.cvtColor(defect, cv2.COLOR_GRAY2BGR)
    cv2.drawContours(output, contours, -1, (0, 255, 0), 2)
    # cv2.imwrite("output.png", output)
    unique_filename = f"processed_{uuid.uuid4().hex}.png"
    output_path = os.path.join("/home/sbna/Documents/WaferGPT-Frontend/processed_image", unique_filename)
    cv2.imwrite(output_path, output)

    if not detected_regions:
        return describe_defect_location("",""),output_path
    return describe_defect_location(detected_regions[0],detected_regions[1]),output_path


if __name__ == '__main__':
    defect_path = r"D:\Defect Detection\png_files\sem9.png"  # Defective wafer image
    # print(locate_sem_defect(defect_path))