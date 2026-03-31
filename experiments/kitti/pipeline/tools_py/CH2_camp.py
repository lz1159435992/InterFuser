#这是用于给udacity_CH2原始数据和预测结果比较的python程序

import csv
import os
from PIL import Image
import subprocess
import numpy as np
# PATH

RIFE_path = "/home/hyf710/documents/RIFE/ECCV2022-RIFE"


# 环境变量

# def
def csv_reader(file_path,i):
    # 初始化存储数据的二维数组
    data_array = []
    # 打开文件并读取内容
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        # 忽视第一行（列名）
        header = next(reader)
        # 遍历剩余行并提取数据
        if(i==0):
            for row in reader:
                data = int(row[0])
                data_array.append(data)
            return data_array
        if(i==1):
            for row in reader:
                data = float(row[1])
                data_array.append(data)
            return data_array

def ang_to_rad(n):
    return n*np.pi/180
def rad_to_ang(n):
    return n*180/np.pi
# main

sum_N = 0
sum_N2 = 0
sum_n = 0
sum_N_ = 0
sum_N2_ = 0
sum_n_ = 0
sum_N_in_N = 0
sum_n_in_N = 0
sum_n_in_n = 0
output_path_0 = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_0_steering_camp.csv"
find_output_path = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/output/test.csv"

find_list = []

for J in range(6):
    I = str(J+1)
    csv_path = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_" + I + "_steering.csv"
    csv_add_path = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_" + I + "_steering_add.csv"
    csv_output_path = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_" + I + "_steering_output.csv"
    csv_add_output_path = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_" + I + "_steering_add_output.csv"
    csv_add_output2_path = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_" + I + "_steering_add_output2.csv"
    output_path = "/home/hyf710/documents/udacity/self-driving-car/datasets/CH2/input/HMB_" + I + "_steering_camp.csv"

    data_array = np.array(csv_reader(csv_path,1))
    data_add_array = np.array(csv_reader(csv_add_path,1))
    data_output_array = np.array(csv_reader(csv_output_path,1))
    data_add_output_array = np.array(csv_reader(csv_add_output_path,1))
    data_add_output2_array = np.array(csv_reader(csv_add_output2_path,1))
    
    max_theta = 0
    min_theta = 0
    max_N = 0
    min_N = 0
    N = len(data_array)
    N2 = N-1
    n = 2*N-1
    number = np.array(range(21))

    delta_N = np.abs(data_output_array - data_array)
    delta_N2 = np.abs(data_add_output2_array - data_add_array[1::2])
    delta_n = np.abs(data_add_output_array - data_add_array)

    N_ = np.sum(delta_N[:, None] < ang_to_rad(number), axis=0)
    N2_ = np.sum(delta_N2[:, None] < ang_to_rad(number), axis=0)
    n_ = np.sum(delta_n[:, None] < ang_to_rad(number), axis=0)

    N_L = data_output_array[1:]
    N_R = data_output_array[:-1]
    N_M = data_add_output2_array
    n_L = data_add_output_array[::2][1:]
    n_R = data_add_output_array[::2][:-1]
    n_M = data_add_output_array[1::2]

    n_in_n = np.sum((n_L[:, None] - ang_to_rad(number)/10 < n_M[:, None]) & (n_M[:, None] < n_R[:, None] + ang_to_rad(number)/10) | (n_R[:, None] - ang_to_rad(number)/10 < n_M[:, None]) & (n_M[:, None] < n_L[:, None] + ang_to_rad(number)/10), axis=0)
    N_in_N = np.sum((N_L[:, None] - ang_to_rad(number)/10 < N_M[:, None]) & (N_M[:, None] < N_R[:, None] + ang_to_rad(number)/10) | (N_R[:, None] - ang_to_rad(number)/10 < N_M[:, None]) & (N_M[:, None] < N_L[:, None] + ang_to_rad(number)/10), axis=0)
    n_in_N = np.sum((N_L[:, None] - ang_to_rad(number)/10 < n_M[:, None]) & (n_M[:, None] < N_R[:, None] + ang_to_rad(number)/10) | (N_R[:, None] - ang_to_rad(number)/10 < n_M[:, None]) & (n_M[:, None] < N_L[:, None] + ang_to_rad(number)/10), axis=0)


    max_theta = np.max(data_array)
    min_theta = np.min(data_array)

    max_index = np.argmax(data_array)
    min_index = np.argmin(data_array)

    if(False):#总和计数部分
        sum_N = sum_N + N
        sum_N2 = sum_N2 + N2
        sum_n = sum_n + n
        sum_N_ = sum_N_ + N_
        sum_N2_ = sum_N2_ + N2_
        sum_n_ = sum_n_ + n_
        sum_n_in_N = sum_n_in_N + n_in_N
        sum_N_in_N = sum_N_in_N + N_in_N
        sum_n_in_n = sum_n_in_n + n_in_n

    if(True):#查找最大值部分
        find = np.where(delta_n>ang_to_rad(10))[0]
        find_d_1 = [csv_reader(csv_add_path,1)[i] for i in find]
        find_i_1 = [I] * len(find)
        find_id_1 = [csv_reader(csv_add_path,0)[i] for i in find]
        find_list.extend(list(map(list, zip(*[find_d_1,find_i_1,find_id_1]))))

    if(False):#输出部分
        output_data_array = []
        output_data_array.append([N,N2,n])
        output_data_array.append([min_index,max_index])
        output_data_array.append([min_theta,max_theta])
        output_data_array.append([rad_to_ang(min_theta),rad_to_ang(max_theta)])
        output_data_array.append(N_)
        output_data_array.append(N2_)
        output_data_array.append(n_)
        output_data_array.append(n_in_N)
        output_data_array.append(N_in_N)
        output_data_array.append(n_in_n)
        output_data_array.append(N_/N)
        output_data_array.append(N2_/N2)
        output_data_array.append(n_/n)
        output_data_array.append(n_in_N/N)
        output_data_array.append(N_in_N/N)
        output_data_array.append(n_in_n/N)

        with open(output_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(output_data_array)

if(True):#find输出部分
    with open(find_output_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(find_list)

if(False):#CSV输出部分
    output_data_array = []
    output_data_array.append([sum_N,sum_N2,sum_n])
    output_data_array.append(sum_N_)
    output_data_array.append(sum_N2_)
    output_data_array.append(sum_n_)
    output_data_array.append(sum_n_in_N)
    output_data_array.append(sum_N_in_N)
    output_data_array.append(sum_n_in_n)
    output_data_array.append(sum_N_/sum_N)
    output_data_array.append(sum_N2_/sum_N2)
    output_data_array.append(sum_n_/sum_n)
    output_data_array.append(sum_n_in_N/sum_N)
    output_data_array.append(sum_N_in_N/sum_N)
    output_data_array.append(sum_n_in_n/sum_N)


    with open(output_path_0, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(output_data_array)