# 建立docker镜像：

```
docker build \
-t autumn \
-f ./docker/autumn/dockerfile \
.
```

# 启动docker镜像：

```
docker run -it \
-v $(pwd)/self-driving-car:/tmp/self-driving-car \
autumn bash
```

# 启动docker镜像(带有X11转发)：

```
docker run -it \
-e DISPLAY=$DISPLAY \
-v $(pwd)/self-driving-car:/tmp/self-driving-car \
-v /tmp/.X11-unix:/tmp/.X11-unix \
-v $HOME/.Xauthority:/root/.Xauthority \
--net=host \
autumn bash
```
