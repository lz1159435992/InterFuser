import os
import cv2
from PIL import Image

# 环境变量
input_path = '/home/hyf710/documents/KITTI/object/training/'
output_path = '/home/hyf710/documents/KITTI/object/training/images_2/'

# 生成视频

#7480
for i in range(7480+1):
    print(i,"/7480=",i/7480)
    img_0 = input_path + 'image_2/' + "%06d" % i + '.png'
    img_1 = input_path + 'prev_2_/' + "%06d" % i + '/1.png'
    img_2 = input_path + 'prev_2/' + "%06d" % i + '_01.png'
    img_3 = input_path + 'prev_2_/' + "%06d" % i + '/2.png'
    img_4 = input_path + 'prev_2/' + "%06d" % i + '_02.png'
    img_5 = input_path + 'prev_2_/' + "%06d" % i + '/3.png'
    img_6 = input_path + 'prev_2/' + "%06d" % i + '_03.png'
    output_video = output_path + "%06d" % i
    if os.path.exists(img_0) and os.path.exists(img_1) and os.path.exists(img_2) and os.path.exists(img_3)  and os.path.exists(img_4) and os.path.exists(img_5) and os.path.exists(img_6):
        if not os.path.exists(output_video):
            os.makedirs(output_video)
        video_0 = output_video + "/"+ "%05d" % 0 + '.jpg'
        video_1 = output_video + "/"+ "%05d" % 1 + '.jpg'
        video_2 = output_video + "/"+ "%05d" % 2 + '.jpg'
        video_3 = output_video + "/"+ "%05d" % 3 + '.jpg'
        video_4 = output_video + "/"+ "%05d" % 4 + '.jpg'
        video_5 = output_video + "/"+ "%05d" % 5 + '.jpg'
        video_6 = output_video + "/"+ "%05d" % 6 + '.jpg'
        Image.open(img_0).save(video_0, 'JPEG')
        Image.open(img_1).save(video_1, 'JPEG')
        Image.open(img_2).save(video_2, 'JPEG')
        Image.open(img_3).save(video_3, 'JPEG')
        Image.open(img_4).save(video_4, 'JPEG')
        Image.open(img_5).save(video_5, 'JPEG')
        Image.open(img_6).save(video_6, 'JPEG')
    
print('done')

