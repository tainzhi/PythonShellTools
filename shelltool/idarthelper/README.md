## release step
- change `util.DEBUG` to false
- change log/config.yaml DEBUG to INFO
## 实现的功能
1. 支持 edge/chrome 的插件
2. idart附件不支持断点续传(idart不支持 Accept-Ranges), 而bug2go/artifacts支持断点续传加速下载, 分成10段并行下载, 至少提升10倍的加速效果
2.1 例如 https://idart.mot.com/browse/IKSWS-126795某次测试中 的 bug2go 普通下载需要 782s, 多断点并行下载只需要34s 

## 分片并发下载对比
[CR1 bug2go](https://idart.mot.com/browse/IKSWS-126807),[CR2 bug2go](https://idart.mot.com/browse/IKSWS-127806)
这两个CR的bug2go都很大(一个700M, 一个1G). 直接在浏览器中下载需要 120s, 通过该工具单线程下载至少700s, 分片并发下载在110s左右

## 其他
- 密码保存在本地
- 查询的项目记录保存在数据库, 会同步到git记录


## Todo
[//]: # (- change db table: add repo name)
[//]: # (- 登录artifacts)
[//]: # (- change regexp)
- release to exe
- [参考: input password with hidden characters](https://www.geeksforgeeks.org/hiding-and-encrypting-passwords-in-python/)
- Download Attachment 右键菜单菜单-重新覆盖下载,规避下载失败的问题
- Download fastboot下载最新的image, 提供 user/userdebug, test-keys/release-keys下载选项
- 下载apk选项
- 不从browser启动, 提供直接启动apk的选项