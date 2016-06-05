from setuptools import setup


setup(name = 'ersatz',
      version = '0.0',
      description = 'A Discrete Event Simulation based on SimPy.',
      author = 'Brett Viren',
      author_email = 'brett.viren@gmail.com',
      license = 'GPLv2',
      url = 'http://github.com/brettviren/erstaz',

      packages = ['ersatz'],

      install_requires=[
          "click",
          "networkx",
      ],

      # entry_points = {
      #     'console_scripts': [
      #         ]
      # }
              
  )

