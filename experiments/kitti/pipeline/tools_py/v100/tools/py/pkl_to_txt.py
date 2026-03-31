import pickle

with open(input(".pkl输入文件位置："), 'rb') as pklin:
    data = pickle.load(pklin)

with open(input(".txt输出文件位置："),"w") as txtout:
    print(data,file = txtout) 