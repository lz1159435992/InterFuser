# 这是给CH2的数据添加三个方向角（原始数据，原始速度，二倍速）指向的python程序
#   标签    原始    插帧    倍速    
#   黑色    红色    绿色    蓝色
import argparse
import scipy.misc
import cv2
import pandas as pd
import os
# path
wheel_path = \
[
"/home/hyf710/documents/udacity/self-driving-car/steering-models/community-models/autumn/wheel.png",
"/home/hyf710/documents/udacity/self-driving-car/steering-models/community-models/autumn/wheel_R.png",
"/home/hyf710/documents/udacity/self-driving-car/steering-models/community-models/autumn/wheel_G.png",
"/home/hyf710/documents/udacity/self-driving-car/steering-models/community-models/autumn/wheel_B.png"
]
# main

parser = argparse.ArgumentParser(description="这是一个给图像添加方向指示的程序")
parser.add_argument("--input_N", type=str, help="输入图像文件夹")
parser.add_argument("--input_n", type=str, help="输入图像id")
parser.add_argument("--n", type=int, help="前后帧数")
parser.add_argument("--output", type=str, help="输出图像位置")
parser.add_argument("--labelR", type=float, help="原始标签")
parser.add_argument("--labelG", type=float, help="预测标签")
parser.add_argument("--labelB", type=float, help="插帧标签")

args = parser.parse_args()

os.mkdir(args.output)

fxy = [2,1.5,1.5,1]
csv_path = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_"+args.input_N+"_steering_add.csv"
df = pd.read_csv(csv_path,dtype=str)
idx = df[df["frame_id"] == args.input_n].index[0]
indexs=[]
for i in range(-args.n,args.n+1):
    indexs.append(df.iloc[idx + i]["frame_id"])
for n in indexs:

    input_path = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_"+args.input_N+"/"+n+".jpg"
    output_path = args.output+n+".jpg"

    result=[]
    if(True):#计算rusult
        csv_path_0 = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_"+args.input_N+"_steering_add.csv"
        df_0 = pd.read_csv(csv_path_0)
        data_dict_0 = dict(zip(df_0['frame_id'].astype(int), df_0["b'steering angle'"].astype(float)))
        angle_0 = data_dict_0.get(int(n))

        csv_path_1 = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_"+args.input_N+"_steering_output.csv"
        df_1 = pd.read_csv(csv_path_1)
        data_dict_1 = dict(zip(df_1['frame_id'].astype(int), df_1["steering_angle"].astype(float)))
        angle_1 = data_dict_1.get(int(n))


        csv_path_2 = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_"+args.input_N+"_steering_add_output2.csv"
        df_2 = pd.read_csv(csv_path_2)
        data_dict_2 = dict(zip(df_2['frame_id'].astype(int), df_2["steering_angle"].astype(float)))
        angle_2 = data_dict_2.get(int(n))


        csv_path_3 = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_"+args.input_N+"_steering_add_output.csv"
        df_3 = pd.read_csv(csv_path_3)
        data_dict_3 = dict(zip(df_3['frame_id'].astype(int), df_3["steering_angle"].astype(float)))
        angle_3 = data_dict_3.get(int(n))

        result = [angle_0 , angle_1 , angle_2 , angle_3]
    full_image = cv2.imread(input_path)
    for i in range(4):
        if(result[i]!=None):
            img = cv2.imread(wheel_path[i], -1)

            img = cv2.resize(img, (0,0), fx=fxy[i], fy=fxy[i], interpolation=cv2.INTER_LINEAR)

            height, width, _ = img.shape
            M = cv2.getRotationMatrix2D((width/2, height/2), result[i] * 180.0 / scipy.pi, 1)
            dst = cv2.warpAffine(img, M, (width, height))

            x_offset = int((full_image.shape[1] - width) / 2)
            y_offset = int(300-height/2)
            new_height = min(height, full_image.shape[0] - y_offset)
            for c in range(0, 3):
                alpha = dst[0:new_height, :, 3] / 255.0
                color = dst[0:new_height, :, c] * (alpha)
                beta = full_image[y_offset:y_offset+new_height, x_offset:x_offset+width, c] * (1.0 - alpha)
                full_image[y_offset:y_offset+new_height, x_offset:x_offset+width, c] = color + beta
    cv2.imwrite(output_path, full_image)
