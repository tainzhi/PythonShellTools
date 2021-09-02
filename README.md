# info
这个仓库包含了我的一些android开发中写的python工具

### genSignedApk
实现的功能参考： https://confluence.mot.com/display/BRSSW/App+Bundle

该module的安装、卸载方法参考如下

具体使用
```shell
# 查看使用说明
genSigendApk -h
```

## install
```shell
# 只测试了mac系统, brew安装请google
# 配置python环境
# brew install python3
# --user为安装在~用户目录， 具体安装到~/.local/bin/目录下
# --record 为安装了哪些文件， 方便卸载
# install后发现没有相关module，那么删除缓存的build文件
python setup.py install --user --record files.txt
```
为了快速下载python的依赖库, 建议替换成国内库
在`~/.pip/pip.conf`(在Windows下是`~/.pip/pip.ini`)中修改为
```
[global]
index-url=http://mirrors.aliyun.com/pypi/simple/

[install]
trusted-host=mirrors.aliyun.com
```
## uninstall
```shell
# pip3 list #查看安装的包名, 为CpSlicePic4Android
# pip3 unisntall packnage-name
cat files.txt |xargs rm -rf
```

## pipenv
```bash
curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
# /usr/local/bin/python3.9
# installed to ~/.local/lib/python3.9
python3.9 get-pip.py --user

# after installed pip, then install pipenv
pip install pipenv
```

### python shell tool
- [click](https://rich.readthedocs.io/en/stable/introduction.html)
- [python prompt](https://python-prompt-toolkit.readthedocs.io/en/latest/pages/asking_for_input.html#history)
- argparse是python内置的官方库. 支持一个参数一次使用有不定长的输入, 与bash通配符（wildcards）结合起来非常方便；而Click无法支持。

### 持久化 pickle vs shelve
[shelve基于pickle， 提供了键值对的操作方式， 更方便](https://stackoverflow.com/questions/4103430/what-is-the-difference-between-pickle-and-shelve)


### 关于跨平台
使用`os.environ`后，linux下的home key为 `HOME`, 而windows下为`HOMEPATH`

怎么确认了？在python shell中
```python
>>> import os
>>> os.environ.key()
```

### terminal cli progressbar
- 推荐用rich, progressbar有多种颜色， 非常漂亮
- 也可以自己基于`sys.stdout.flush()`来实现
- tqdm也可以实现， 但是颜色单一。 tqdm作为老牌的Python进度条工具，循环处理、多进程、多线程、递归处理等都是支持的, 
[参考](https://www.cnblogs.com/liuzaoqi/p/13041394.html)
  
### file文件操作， copy/remove操作
- [shutil](https://docs.python.org/3.9/library/shutil.html)
- [os.path](https://docs.python.org/3.9/library/os.path.html)

### 用python执行shell命令
推荐用subprocess.call

[参考](https://www.cnblogs.com/wqbin/p/11759396.html)

### 执行shell命令
- `subprocess.call()` `java -jar`需要用tuple， 不能直接用string
- `subprocess.call()`返回结果为0， 1， 2. 0正确执行， 1正在执行， 用于progressbar
- 不要使用`~/Downloads`目录，因为无法识别`~`

#### 获取当前用户的主目录路径
```python
import os

print (os.environ['HOME'])
print (os.path.expandvars('$HOME'))
print (os.path.expanduser('~'))
```
打印结果全是
> /home/Qin

## python
### python安装在本地local目录
- sudo安装的python的可执行命令包括python, pip3, pipenvc在`/usr/local/bin/python`,
而python包在`/usr/local/lib/python`下
  
- 不需要sudo权限， 安装python在本地目录。 官网下载源码后， 解压
```python
./configure --prefix=~/.python3.9.6
make -j16
make install
```
安装在`~/.python3.9.6`目录下。这中方法已经安装好了pip3

```python
# 如果需要安装pipenv
pip3 install pipenv
# 最终安装到~/.local/bin/目录下
```
- 在zshrc或者bashrc中需要添
```
export PATH="${HOME}/.local/bin:${HOME}/.python3.9.6/bin:$PATH"
```

### [Python name style](https://www.python.org/dev/peps/pep-0008/#package-and-module-names)
- Package and modules names: short, all-lowercase names wiht underscores 
- Class Names: use CapWords
- Functions and Variable names: be lowercase, with words separated by underscore as necessary to improve readability

### 遇到问题
####  no module after reinstall
delete all build cache directories

#### No module named '_ctypes'
```bash
sudo apt install libffi-dev

```
然后, 重新再安装python

#### use pip3, No module named 'lsb_release'
[reference](https://www.pynote.net/archives/592)

寻找Ubunbu自带的Python3使用的 lsb_release 模块，然后将这个模块copy到我们自己编译安装的Python3的lib目录下

```shell
$ sudo cp /usr/lib/python3/dist-packages/lsb_release.py /usr/local/python-3.7/lib/python3.7/
```


### [python modules](https://docs.python.org/3/tutorial/modules.html)
一个文件就是一个module， 文件名就是module名， 
通过import导入module或者module中的定义， 方法

目录下面的`__init__.py`可以为空，使得当前目录变成package。
`__init__.py`中也可以添加package初始化操作或者设置`__all__`变量


### python不推荐使用lambda
- [参考](https://www.python.org/dev/peps/pep-0008/)


### click && setuptools
- [reference](https://click.palletsprojects.com/en/8.0.x/setuptools/)
