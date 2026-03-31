#这是用于给udacity_CH2插帧的python程序

import csv
import os
from PIL import Image
import subprocess

# PATH

RIFE_path = "/home/hyf710/documents/RIFE/ECCV2022-RIFE"


# 环境变量

# def
def csv_reader(file_path):
    # 初始化存储数据的二维数组
    data_array = []
    # 打开文件并读取内容
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        # 忽视第一行（列名）
        header = next(reader)
        # 遍历剩余行并提取数据
        for row in reader:
            timestamp = int(row[0])  # 时间戳转换为整数
            steering_angle = float(row[1])  # 转向角度转换为浮点数
            # 将时间戳和转向角度作为子列表存入二维数组
            data_array.append([timestamp, steering_angle])
    # 输出结果
    return data_array

def insert(jpg_0_path,jpg_1_path,jpg_0_1_path):
    os.chdir(RIFE_path)
    command = ["python3",
    "inference_img.py",
    "--img",jpg_0_path,jpg_1_path,
    "--exp=1"]
    subprocess.run(command, check=True, text=True, capture_output=True)
    img = Image.open("/home/hyf710/documents/RIFE/ECCV2022-RIFE/output/img1.png")
    img.save(jpg_0_1_path,format='JPEG')



# main

for j in range(6):
    I = str(j+1)
    csv_path = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_" + I + "_steering.csv"
    input_path = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_" + I + "_old/"
    output_path = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_" + I + "/"
    csv_output_path = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_" + I + "_steering_add.csv"
    csv_output_path2 = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_" + I + "_steering_add2.csv"

    data_array = csv_reader(csv_path)
    N = len(data_array)
    output_data_array = [['frame_id', "b'steering angle'"]]
    output_data_array2 = [['frame_id', "b'steering angle'"]]
    for i in range(N-1):
        print(I,data_array[i+0][0])
        print(i,"/",N,"=",i/N)
        jpg_0_path = input_path + str(data_array[i+0][0]) + ".jpg"
        jpg_1_path = input_path + str(data_array[i+1][0]) + ".jpg"
        id = int((data_array[i+0][0] + data_array[i+1][0])/2)
        angle = float((data_array[i+0][1] + data_array[i+1][1])/2)
        output_data_array.append([data_array[i+0][0], data_array[i+0][1]])
        output_data_array.append([id, angle])
        output_data_array2.append([id, angle])
        jpg_0_1_path = output_path + str(id) + ".jpg"
        insert(jpg_0_path,jpg_1_path,jpg_0_1_path)
    output_data_array.append([data_array[N-1][0], data_array[N-1][1]])
    with open(csv_output_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(output_data_array)
    with open(csv_output_path2, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(output_data_array2)
