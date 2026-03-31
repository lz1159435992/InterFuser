import pickle
import os
import sys

# {
#     'name':array(['Car'],dtype='<U3'),
#     'truncated':array([0.]),
#     'occluded':array([0.]),
#     'alpha':array([-1.665755],dtype=float32),
#     'bbox':array([[760.1832,165.19519,809.64374,204.37984]],dtype=float32),
#     'dimensions':array([[3.7387738,1.4933319,1.5906806]],dtype=float32),
#     'location':array([[7.0298257,1.2011541,29.458216]],dtype=float32),
#     'rotation_y':array([-1.434138],dtype=float32),
#     'score':array([0.63953483],dtype=float32),
#     'boxes_lidar':array([[29.743713,-7.0150485,-1.03969,3.7387738,1.5906806,1.4933319,-0.13665843]],dtype=float32),
#     'frame_id':'000001'
#


input_pkl=sys.argv[1]
output_dir=sys.argv[2]
with open(input_pkl, 'rb') as pklin:
    datas = pickle.load(pklin)


if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for data in datas:
    with open(output_dir+'/'+data['frame_id']+".txt","w") as txtout:
        for i in range(len(data['name'].tolist())):
            print(data['name'].tolist()[i]
            ,data['truncated'].tolist()[i]
            ,data['occluded'].tolist()[i]
            ,data['alpha'].tolist()[i]
            ,data['bbox'].tolist()[i][0]
            ,data['bbox'].tolist()[i][1]
            ,data['bbox'].tolist()[i][2]
            ,data['bbox'].tolist()[i][3]
            #这里调换下1、3位，我也不知道为什么，反正就是要换
            ,data['dimensions'].tolist()[i][2]
            ,data['dimensions'].tolist()[i][1]
            ,data['dimensions'].tolist()[i][0]
            ,data['location'].tolist()[i][0]
            ,data['location'].tolist()[i][1]
            ,data['location'].tolist()[i][2]
            ,data['rotation_y'].tolist()[i]
            ,data['score'].tolist()[i]
#            ,data['boxes_lidar'].tolist()[i][0-6]
            ,file = txtout)

print("完成")
# with open(output_dir,"w") as txtout:
#     print(data,file = txtout) 