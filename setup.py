import setuptools


def main():
    setuptools.setup(
        name='picameleon',
        packages=["picameleon", "picameleon.outputs"],
        include_package_data=True,
        platforms='ALL',
        version='0.0.2',
        license='LGPLv3',
        description='A python client or picameleon',
        author='André Esser',
        author_email='bepandre@hotmail.com',
        url='https://github.com/Esser50K/PiCameleon',
        download_url='https://github.com/Esser50K/PiCameleon/archive/refs/tags/picameleon-client-v0.0.2.tar.gz',
        keywords=['picamera', 'service', 'raspberrypi'],
        install_requires=[],
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            'Topic :: Software Development :: Build Tools',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
        ],
    )


if __name__ == '__main__':
    main()
