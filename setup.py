from setuptools import setup, find_packages

setup(
    name='requests_proxy_rotation',
    version='0.1.0',
    author='phannt',
    author_email='phan123123@gmail.com',
    description='A wrapped version of requests. Allow automatic rotate proxy with limit of each endpoint',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    install_requires=[
        'requests',
    ],
    license='Apache License 2.0',
    license_files=('LICENSE',),
    keywords='python library requests proxy rotation', 
)
