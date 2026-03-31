from PIL import Image
import os

Input="/home/hyf710/documents/KITTI/object/training/image_2"
Output="/home/hyf710/documents/KITTI/object_/training/image_2"

imgs=os.listdir(Input)
imgs.sort()
for img in imgs:
    print(img)
    input_path=os.path.join(Input,img)
    output_path=os.path.join(Output,img)
    img_in=Image.open(input_path)
    img_out=img_in.resize((int(img_in.size[0]/2),int(img_in.size[1]/2)))
    img_out.save(output_path)