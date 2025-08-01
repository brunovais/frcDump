from setuptools import setup, find_packages

setup(
    name='frcDump',
    version='0.1',
    packages=find_packages(),
    install_requires=["requests","PyYAML"],  # requirements.txt
    entry_points={
        'console_scripts': [
            'frcDump=frcDump.main:main',
        ],
    },
    author='Bruno Vais',
    author_email='your_email@exemple.com',
    description='Description of frcDump.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/brunovais/frcDump',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
