import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim


def compare_images( img_path):
    ideal_path = "/home/sbna/Documents/WaferGPT-Backend/png_files/sem4.png"  # Ideal wafer image
    # Load images as grayscale
    img1 = cv2.imread(ideal_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

    if img1 is None or img2 is None:
        print("Error loading images")
        return None

    # Resize images to the same size if needed
    img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    # Compute SSIM
    score, diff = ssim(img1, img2, full=True)
    diff = (diff * 255).astype("uint8")  # Convert to uint8 for visualization

    print(f"SSIM Score: {score:.4f}")

    # Display difference
    # cv2.imshow("Difference", diff)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    return score

# ll=[8,9,10,12,13,15,16,17,18,19,21,22,1,6,7]
# for i in ll:
#     # Example usage
#     ideal_image = r"D:\Defect Detection\png_files\sem4.png"
#     defect_image = f"D:\Defect Detection\png_files\sem{i}.png"
#     similarity_score = compare_images(ideal_image, defect_image)
#     print(similarity_score)



