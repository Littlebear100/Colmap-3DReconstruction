import cv2
import os
import json
from multiprocessing import Pool, Manager

class ImageProcessor:
    def __init__(self, config, progress_queue=None):
        self.input_folder = config["input_folder"]
        self.output_folder = config["output_folder"]
        self.progress_queue = progress_queue

    def process_images(self):
        filenames = [f for f in os.listdir(self.input_folder) if f.lower().endswith((".jpg", ".png"))]
        if self.progress_queue:
            self.progress_queue.put(f"Found {len(filenames)} images to process.")
        with Pool() as pool:
            pool.map(self.process_image, filenames)
        if self.progress_queue:
            self.progress_queue.put("Image processing completed.")

    def process_image(self, filename):
        img_path = os.path.join(self.input_folder, filename)
        try:
            image = cv2.imread(img_path)
            if image is None:
                if self.progress_queue:
                    self.progress_queue.put(f"Failed to read image: {img_path}")
                return
            output_path = os.path.join(self.output_folder, filename)
            cv2.imwrite(output_path, image)
            if self.progress_queue:
                self.progress_queue.put(f"Processed and saved: {output_path}")
        except Exception as e:
            if self.progress_queue:
                self.progress_queue.put(f"Error processing image {img_path}: {e}")

if __name__ == "__main__":
    with open("config.json", "r") as f:
        config = json.load(f)
    manager = Manager()
    progress_queue = manager.Queue()
    processor = ImageProcessor(config, progress_queue)
    processor.process_images()
    print("Image processing completed.")
