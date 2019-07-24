import setuptools

setuptools.setup(
    name='Haruhi-Script',
    version='0.8',
    author='je09',
    author_email='je09@yandex.ru',
    description='A simple parser/downloader of/from mangadex.org',
    url='https://github.com/je09/Haruhi-Script',
    packages=['src'],
    install_requires=[
        'click==7.0',
        'requests==2.22.0'
    ],
    entry_points={
        'console_scripts': [
            'haruhi = src.haruhi_script:main'
        ]
    },
    classifiers={
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: MIT License'
    }
)