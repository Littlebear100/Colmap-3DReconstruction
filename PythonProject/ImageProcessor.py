import cv2
import os
import json
import logging
from multiprocessing import Pool

class ImageProcessor:
    def __init__(self, config):
        self.input_folder = config["input_folder"]
        self.output_folder = config["output_folder"]
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
            output_path = os.path.join(self.output_folder, filename)
            cv2.imwrite(output_path, image)
            logging.info(f"Processed and saved: {output_path}")
        except Exception as e:
            logging.error(f"Error processing image {img_path}: {e}")

if __name__ == "__main__":
    with open("config.json", "r") as f:
        config = json.load(f)
    processor = ImageProcessor(config)
    processor.process_images()
