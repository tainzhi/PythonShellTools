from setuptools import setup

setup(
    name="cp4AndroidDev",
    version='0.2',
    py_modules=['cp_slice_pic_4_android'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        cpad=cp_slice_pic_4_android:cp
    '''
)