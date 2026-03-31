#这是针对samurai的辅助脚本

#import

import os
import sys

# 环境变量

samurai_path = "/home/hyf710/documents/samurai"
samurai_output_path = samurai_path + "/output.txt"
temp_path = "/home/hyf710/Temp/temp.txt"

#def

def predict(video_dir, bbox):
    #bbox->xywh
    xywh = [bbox[0],bbox[1],bbox[2]-bbox[0],bbox[3]-bbox[1]]
    #写xywh到temp文件
    with open(temp_path, 'w') as f:
        print(xywh[0],",",xywh[1],",",xywh[2],",",xywh[3], file=f)
    #预测
    call="python scripts/demo.py"\
    +" --video_path " + video_dir\
    +" --txt_path " + temp_path
    
    os.chdir(samurai_path)
    os.system(call)
    #读取output文件内容
    with open(samurai_output_path, 'r') as f:
        gt = f.readlines()
    x, y, w, h = map(float, gt[0].split(','))
    x, y, w, h = int(x), int(y), int(w), int(h)
    #xywh->bbox
    output_bbox = [x , y , x+w , y+h]
    return output_bbox

def predict_i(a_z_dir, z_a_dir, label_path, result_path):
    if os.path.exists(a_z_dir) and os.path.exists(z_a_dir) and os.path.exists(label_path):
        file = open(label_path,"r")
        lines_first=[]
        lines_else=[]
        lines = file.readlines()
        #读取
        for line in lines:
            line_ = line.split()
            if(len(line_)!=0):
                lines_first.append(line_[0])
                line_else = []
                for i in range(len(line_)-1):
                    line_else.append(float(line_[i+1]))
                lines_else.append(line_else)
        #处理&输出
        sys.stdout = open(result_path, 'w')
        for i in range(len(lines_first)):
            if lines_first[i]=='Car':
                print(lines_first[i],end=' ')
                box = lines_else[i][3:7]
                result = predict(z_a_dir, predict(a_z_dir, box))
                print("0.00 0 0.00",end=' ')
                print("%.2f" % result[0],end=' ')
                print("%.2f" % result[1],end=' ')
                print("%.2f" % result[2],end=' ')
                print("%.2f" % result[3],end=' ')
                print("0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.99")
        sys.stdout = sys.__stdout__
    #return void

#PATH

label_path_dir = '/home/hyf710/documents/KITTI/object/training/label_2/'
a_z_dir_path_dir = '/home/hyf710/documents/KITTI/object/training/video_2/0246/'
z_a_dir_path_dir = '/home/hyf710/documents/KITTI/object/training/video_2/6420/'
result_path_dir = '/home/hyf710/documents/output/output_9/result/data/'


#main
i = int(sys.argv[1])
print(i)
label_path = label_path_dir + "%06d" % i + '.txt'
a_z_dir_path = a_z_dir_path_dir + "%06d" % i
z_a_dir_path = z_a_dir_path_dir + "%06d" % i
result_path = result_path_dir + "%06d" % i +'.txt'
predict_i(a_z_dir_path, z_a_dir_path, label_path, result_path)
print('done')
