# info
这个仓库包含了我的一些android开发中写的python工具


## install
```shell
# 只测试了mac系统, brew安装请google
brew install python3
pip3 install --editable .

```
为了快速下载python的依赖库, 建议替换成国内库
在`~/.pip/pip.conf`中修改为
```
[global]
index-url=http://mirrors.aliyun.com/pypi/simple/

[install]
trusted-host=mirrors.aliyun.com
```
## uninstall
```shell
pip3 list #查看安装的包名, 为CpSlicePic4Android
pip3 unisntall CpSlicPic4Android
```