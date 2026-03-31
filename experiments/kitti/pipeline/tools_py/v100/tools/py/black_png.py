import cv2
import numpy as np
import os


inputPath="/Hyf/KITTI/object/training/image_2"
outputPath="/Hyf/KITTI/object_4/training/image_2"


files = os.listdir(inputPath)
files.sort()
for file in ["000000.png"]:
    print(file)
    input_path = os.path.join(inputPath, file)
    output_path = os.path.join(outputPath, file)

    image_in = cv2.imread(input_path)
    image_out = np.zeros(image_in.shape, dtype = np.uint8)

    
    cv2.imwrite(output_path,image_out)
