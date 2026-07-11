import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'gesture_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # 🔥 이 줄이 추가되어 models 폴더 내의 .task 파일을 빌드 경로(install/)로 복사합니다.
        (os.path.join('share', package_name, 'models'), glob('models/*.task')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nongsa',
    maintainer_email='lsm123727@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'gesture_node = gesture_control.test:main',
        ],
    },
)