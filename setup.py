from setuptools import setup, find_packages

setup(
    name='shared_folder_opu',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A short description of your package',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    # url='https://github.com/yourusername/shared_folder_opu',
    packages=find_packages(),
    install_requires=[
        # List your package dependencies here
        # For example, 'requests>=2.25.1'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
