import cv2
import os
import json
import numpy as np
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
            processed_image = self.enhance_image(image)
            output_path = os.path.join(self.output_folder, filename)
            cv2.imwrite(output_path, processed_image)
            if self.progress_queue:
                self.progress_queue.put(f"Processed and saved: {output_path}")
        except Exception as e:
            if self.progress_queue:
                self.progress_queue.put(f"Error processing image {img_path}: {e}")

    def enhance_image(self, image):
        # 图像锐化（稍微调整）
        sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        image = cv2.filter2D(image, -1, sharpen_kernel)

        # 去噪（减少强度）
        image = cv2.fastNlMeansDenoisingColored(image, None, 3, 3, 7, 21)

        # 直方图均衡化（保持不变）
        img_yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
        img_yuv[:, :, 0] = cv2.equalizeHist(img_yuv[:, :, 0])
        image = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)

        # 图像缩放（保持原分辨率）
        scale_percent = 100
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)
        image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

        # 颜色校正（保持不变）
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        image = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        return image


if __name__ == "__main__":
    with open("config.json", "r") as f:
        config = json.load(f)
    manager = Manager()
    progress_queue = manager.Queue()
    processor = ImageProcessor(config, progress_queue)
    processor.process_images()
    print("Image processing completed.")
