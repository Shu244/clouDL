from setuptools import setup, find_packages

setup(
    name='clouDL',
    version='0.1.1',
    author="Shuhao Lai",
    author_email="Shuhaolai18@gmail.com",
    description="Automatically manages a cluster of VMs in GCP to train and hyperparamter tune DL models that use PyTorch.",
    packages=find_packages(include=['clouDL', 'clouDL.*', 'clouDL_utils', 'clouDL_utils.*']),
    install_requires=[
        'google-api-python-client',
        'google-cloud-storage',
        'matplotlib',
        'pathlib'
    ],
    entry_points={
        'console_scripts': [
            'clouDL=clouDL.main:main',
            'clouDL_create=clouDL.main:create_user_files',
            'clouDL_analyze=clouDL.analyze:main'
        ]
    },
    package_data={'clouDL_utils': ['user_files/*', 'startup.sh']},
)