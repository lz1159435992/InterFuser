import os
import sys

Input="/Hyf/KITTI/object/training/label_2"
Output="/Hyf/KITTI/object/training/label_2%2"
T=[1,1,1,.5,.5,.5,.5,1,1,1,1,1,1,1]
#__^_^_^,__2_D__,____3D_____,^

labels=os.listdir(Input)
labels.sort()
for label in labels:
    print(label)
    input_path=os.path.join(Input,label)
    output_path=os.path.join(Output,label)

    file = open(input_path,"r")
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
    #转换
    for i in range(len(lines_else)):
        for j in range(len(lines_else[i])):
            lines_else[i][j]=lines_else[i][j]*T[j]
    #输出
    # print(lines_else)
    sys.stdout = open(output_path, 'w')
    for i in range(len(lines_else)):
        print(lines_first[i],end=' ')
        for j in range(len(lines_else[i])):
            print("%.2f" % lines_else[i][j],end=' ')
        print()
    sys.stdout = sys.__stdout__