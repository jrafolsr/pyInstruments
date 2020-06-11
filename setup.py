from setuptools import setup

setup(name='pyLab',
      version='0.0',
      description='A package to control lab sourcemeters, multimeters and DAQs',
      url='http://github.com/jrafolsr/lab-instrumentation',
      author='Joan Ràfols Ribé',
      author_email='joanrafols1988@gmail.com',
      license='MIT',
      packages=['pyLab_v2'],
      install_requires=[
          'visa', 'PyDAQmx'
      ],
      zip_safe=False)