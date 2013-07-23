try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

import os
import sys

#brutal hack, nuff said
if len(sys.argv)>=2 and sys.argv[1]=='install':
    DIRS = ('./parseryml/other/ARHIVES', 
            './parseryml/other/hashes', 
            './parseryml/other/IMG', 
            './parseryml/other/IMG_OUT', 
            './parseryml/other/IMG_OUT/128x80', 
            './parseryml/other/IMG_OUT/213x168', 
            './parseryml/other/IMG_OUT/98x83', 
            './parseryml/other/OLD_YML',
            './parseryml/other/YML')
    for dir in DIRS:
        print "create folder: %s" % dir
        if not os.path.exists(dir):
            os.makedirs(dir)


setup(
    name='ParserYML',
    version='0.1',
    description='',
    author='',
    author_email='',
    url='',
    install_requires=[
        "Pylons>=1.0",
        "elementtree",
	"pymongo",
	"celery",
	"amqplib",
    ],
    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'parseryml': ['i18n/*/LC_MESSAGES/*.mo']},
    zip_safe=False,
    paster_plugins=['PasteScript', 'Pylons'],
    entry_points="""
    [paste.app_factory]
    main = parseryml.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)


