import os
import sys

Input="/Hyf/KITTI/object/training/calib"
Output="/Hyf/KITTI/object/training/calib%2"
T=[2,0,2,2,0,2,2,2,0,0,1,1]
t=[0,0,0,0,0,0,0,0,0,0,0,0]

calibs=os.listdir(Input)
calibs.sort()
for calib in calibs:
    print(calib)
    input_path=os.path.join(Input,calib)
    output_path=os.path.join(Output,calib)

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
    for i in range(4):
        for j in range(12):
            lines_else[i][j]=lines_else[i][j]*T[j]+t[j]
    #输出
    # print(lines_else)
    sys.stdout = open(output_path, 'w')
    for i in range(7):
        print(lines_first[i],end=' ')
        for j in range(len(lines_else[i])):
            print("%e" % lines_else[i][j],end=' ')
        print()
    sys.stdout = sys.__stdout__