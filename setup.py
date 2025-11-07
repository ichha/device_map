from setuptools import setup, find_packages

version = '0.1.4'
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='netbox-plugin-device-map',
    version=version,
    description='A simple device map with filter criteria',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    author='Victor Golovanenko',
    author_email='drygdryg2014@yandex.com',
    url='https://github.com/drygdryg/netbox-plugin-device-map',
    download_url=f'https://github.com/drygdryg/netbox-plugin-device-map/archive/v{version}.zip',
    python_requires='>=3.10',
    install_requires=['netbox>=4.0'],
    classifiers=[
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: MIT License',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration'
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
