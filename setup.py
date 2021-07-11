from setuptools import setup, find_packages

setup(
    name="python_shell_tool",
    version='0.0.1',
    author='tainzhi',
    author_email='qfq61@qq.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'rich',
    ],
    entry_points={
        'console_scripts':[
            'genSignedBundleApk=shelltool.bundle:bundle_generate'
        ]
    }
)
