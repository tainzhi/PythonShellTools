from setuptools import setup, find_packages

import shelltool.adb


setup(
    name="python_shell_tool",
    version='0.0.1',
    author='tainzhi',
    description='shell tools by python',
    url='https://github.com/tainzhi/PythonShellTools',
    author_email='qfq61@qq.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'rich',
        'selenium',
    ],
    entry_points={
        'console_scripts':[
            'genSignedApk=shelltool.bundle:bundle_generate',
            'logh=shelltool.loghelper:download',
        ]
    }
)
