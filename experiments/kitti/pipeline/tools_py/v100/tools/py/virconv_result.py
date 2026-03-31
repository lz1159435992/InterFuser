import os
import numpy as np
import sys


dir=sys.argv[1]
inputdir=dir+"/VirConv.txt"
outputdir=dir+"/result.csv"


results=[]
with open(inputdir, 'r') as file:
    lines = file.readlines()
    for line in lines:
        line = line.strip()
        line_float = []
        for num in line.split():
            line_float.append(float(num))
        results.append(line_float)

results=np.transpose(results).tolist()
print(results)
result_average=[]
result_std=[]
result_max=[]
result_min=[]
for result in results:
    result_average.append(np.average(result))
    result_std.append(np.std(result))
    result_max.append(np.max(result))
    result_min.append(np.min(result))

with open(outputdir, 'w') as file:
    print(result_average, file=file)
    print(result_std, file=file)
    print(result_max, file=file)
    print(result_min, file=file)