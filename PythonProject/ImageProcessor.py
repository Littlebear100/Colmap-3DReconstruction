import cv2
import os
import json
import logging
import numpy as np
from multiprocessing import Pool

class ImageProcessor:
    def __init__(self, config):
        self.input_folder = config["input_folder"]
        self.output_folder = config["output_folder"]
        self.apply_denoise = config.get("apply_denoise", True)
        self.apply_enhance = config.get("apply_enhance", True)
        self.apply_sharpen = config.get("apply_sharpen", True)
        logging.basicConfig(level=logging.INFO)

    def process_images(self):
        filenames = [f for f in os.listdir(self.input_folder) if f.lower().endswith((".jpg", ".png"))]
        with Pool() as pool:
            pool.map(self.process_image, filenames)

    def process_image(self, filename):
        img_path = os.path.join(self.input_folder, filename)
        try:
            image = cv2.imread(img_path)
            if image is None:
                logging.error(f"Failed to read image: {img_path}")
                return
            processed_image = self.preprocess_image(image)
            output_path = os.path.join(self.output_folder, filename)
            cv2.imwrite(output_path, processed_image)
            logging.info(f"Processed and saved: {output_path}")
        except Exception as e:
            logging.error(f"Error processing image {img_path}: {e}")

    def preprocess_image(self, image):
        processed_image = image
        # 图像去噪
        if self.apply_denoise:
            processed_image = cv2.fastNlMeansDenoisingColored(processed_image, None, 10, 10, 7, 21)

        # 图像增强
        if self.apply_enhance:
            lab = cv2.cvtColor(processed_image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b))
            processed_image = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # 锐化
        if self.apply_sharpen:
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            processed_image = cv2.filter2D(processed_image, -1, kernel)

        return processed_image

if __name__ == "__main__":
    with open("config.json", "r") as f:
        config = json.load(f)
    processor = ImageProcessor(config)
    processor.process_images()