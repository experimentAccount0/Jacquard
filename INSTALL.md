Installing Jaquard
================

###Prerequisites

* Jacquard has been tested python 2.7 on Windows7, OSX, and Unix.
* natsort (3.5.2) and numpy (>=1.7.1) are required 
* nosetests and testfixtures (3.0.2) are required for running automated tests
* Note that pip installs all required libraries; see [Installing] below.

###Installing
The easiest way to install Jacquard is through PyPI system. Get pip if it's not available in your system:

`$ pip install jacquard`

You can install from source as root by cloning from github and running:

`$ python setup.py install`

and if you don't have root permissions, you can install locally:

`$ python setup.py install --prefix /home/your_username/`

And you can run the automated suite of unit tests to confirm installation:

`$ python setup.py test`