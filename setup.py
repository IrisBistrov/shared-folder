from setuptools import setup, find_packages

setup(
    name='shared_folder_opu',
    version='0.1.0',
    author='Iris Bistrov and Hila Ramati',
    description='a package that implements shared folder client and server',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        "pytest==7.4.4",
        "randomname~=0.2.1",
        "setuptools~=69.0.3",
        "watchdog~=3.0.0",
        "rich~=13.7.0"
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)
