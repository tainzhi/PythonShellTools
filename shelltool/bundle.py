#!/usr/bin/python3

import os
import click
import subprocess
from shelltool import config
from shelltool.db import DB
from rich.progress import Progress
from rich.progress import BarColumn


@click.command()
@click.option('-t', '--tool', 'bundle_tool', required=False,
              help='google bundle tool')
@click.option('-d', '--device', 'device', required=False,
              help='需要打包device平台的signed apk')
@click.option('-e', '--key', 'key_store', required=False,
              help='key store file'
              )
@click.option('-o', '--output', 'output', required=False,
              help='default output dir is ~/Downloads'
              )
@click.option('-g', '--gradle', is_flag=True,
              help="whether to gradle MotCamera:MotCamera:bundleDebug")
# ROOT_DIR=$(pwd)
# AabDir="$ROOT_DIR"/MotCamera/build/outputs/bundle/debug
# aabFile="/home/FQ1/StudioProjects/MotCamera3/MotCamera/build/outputs/bundle/debug/MotCamera3-v8.0.63.80-debug.aab"
# BundleTool="/home/FQ1/workspace/bundletool-all-1.6.1.jar"
# Device="borneo"
# DeviceSpecsJson="$ROOT_DIR"/MotCamera/bundleConfig/deviceSpecs/"$Device".json
# KeyStoreFile="$ROOT_DIR"/tools/certs/common2.keystore
# Modules="vendor_${Device}"
# OutputDir="cd ~/Downloads/"
#
# java -jar $BundleTool build-apks --mode=system --bundle=$aabFile --output=Set.apks --overwrite --device-spec=$DeviceSpecsJson --modules=$Modules --ks $KeyStoreFile --ks-key-alias common2 --key-pass pass:motorola --ks-pass pass:motorola
#
# java -jar $BundleTool extract-apks --apks=Set.apks --output-dir=./ --device-spec=$DeviceSpecsJson
#
def bundle_generate(bundle_tool, device, key_store, output, gradle):
    db = DB(config.config_path)
    # todo
    # root_dir = os.getcwd()
    root_dir = '/home/FQ1/StudioProjects/MotCamera3'
    if not gradle:
        # 1.1 bundle_tool使用默认的， 从配置中读取
        if bundle_tool is None:
            bundle_tool = db.get_bundle_tool()
            # 1.2 bundle_tool从配置中读取失败
            if bundle_tool is None or not os.path.exists(bundle_tool):
                click.prompt("config bundle tool path is invalid, please input new path")
        # 2.1 bundle_tool使用新输入的， 并验证是否存在， 地址是否正确
        else:
            if not os.path.exists(bundle_tool):
                click.prompt("Please input bundle tool path correctly")
            # 2.2 bundle_tool写入config中
            else:
                db.save_bundle_tool(bundle_tool)

        if device is None:
            device = db.get_device()
            # todo 通过读取列表， 判断device是否输入正确
        else:
            db.save_device(device)

        if key_store is None:
            key_store = db.get_key_store()
        else:
            db.save_key_store(key_store)

        if output is None:
            saved_output = db.get_output()
            if saved_output is None:
                output = config.default_output
        else:
            db.save_output(output)

        aab = get_aab(root_dir)
        # 获取MotCamera3-v8.0.63.80-debug.aab文件的无后缀名字
        aab_basename = os.path.basename(aab)
        aab_name_without_extention = aab_basename[0:aab_basename.rindex('.')]
        if aab is None:
            click.prompt('aab不存在， 请重新构建')

        device_json = os.path.join(root_dir, 'MotCamera/bundleConfig/deviceSpecs/{}.json'.format(device))
        modules = 'vendor_{}'.format(device)
        tmp_apks = os.path.join(output, 'bundle_tmp.apks')

        with Progress(
                "[progress.description]{task.description}",
                BarColumn(),
        ) as progress:
            task = progress.add_task("[red]Generating tmp apks", start=False, completed=100)
            ret = 1
            while not progress.finished and ret == 1:
                # java -jar /home/FQ1/workspace/bundletool-all-1.6.1.jar build-apks --mode=system --bundle=/home/FQ1/StudioProjects/MotCamera3/MotCamera/build/outputs/bundle/debug/MotCamera3-v8.0.64.80-debug.aab --output=Set.apks --overwrite --device-spec=/home/FQ1/StudioProjects/MotCamera3/MotCamera/bundleConfig/deviceSpecs/berlin.json --modules=vendor_berlin --ks /home/FQ1/StudioProjects/MotCamera3/tools/certs/common2.keystore --ks-key-alias common2 --key-pass pass:motorola --ks-pass pass:motorola
                ret = subprocess.call(["java", "-jar", bundle_tool, "build-apks", "--mode=system",
                                       "--bundle={}".format(aab), "--output={}".format(tmp_apks), "--overwrite",
                                       "--device-spec={}".format(device_json), "--modules={}".format(modules),
                                       "--ks", key_store,
                                       "--ks-key-alias", "common2",
                                       "--key-pass", "pass:motorola",
                                       "--ks-pass", "pass:motorola",
                                       ])
        click.echo("成功生成{}".format(tmp_apks))

        with Progress(
                "[progress.description]{task.description}",
                BarColumn(),
        ) as progress:
            task = progress.add_task("[red]Generating system.apk", start=False, completed=100)
            ret = 1
            while not progress.finished and ret == 1:
                # java -jar $BundleTool extract-apks --apks=Set.apks --output-dir=./ --device-spec=$DeviceSpecsJson
                # 该命令会在output目录下生成 system.apk
                ret = subprocess.call(['java', '-jar',
                                       bundle_tool, 'extract-apks',
                                       '--apks={}'.format(tmp_apks),
                                       '--output-dir={}'.format(output),
                                       '--device-spec={}'.format(device_json)])
        click.echo("成功生成{}".format(os.path.join(output, 'system.apk')))
        target_apk = "{}_{}.apk".format(aab_name_without_extention, device)
        os.rename(os.path.join(output, 'system.apk'), os.path.join(output, target_apk))
        click.echo("已经生成最终signed bundle apk: {}".format(os.path.join(output, target_apk)))
    else:
        ret = subprocess.call('./gradlew MotCamera:MotCamera:bundleDebug')


def get_aab(root_dir):
    parent_dir = os.path.join(root_dir, 'MotCamera/build/outputs/bundle/debug/')
    aab = ""
    for file in os.listdir(parent_dir):
        if file.endswith('.aab'):
            aab = file
            return os.path.join(parent_dir, aab)
    # 不存在aab， 需要重新构建
    return None
