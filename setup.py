from setuptools   import setup

setup(name = 'VidUtils',
      version='0.1.2',
      description='Useful Python Video Writing and Reading Utilities',
      author='Jon Pajaud',
      author_email='jpajaud2@gmail.com',
      packages = ['vidutils'],
      package_data={'vidutils':['DocStrings/*.txt']}
)

# run python setup.py bdist_egg
# resulting egg in in ./dist/ directory
