# recipes
### Usage:
Install Python 3.8.5 or greater, you can do it via pyenv https://github.com/pyenv/pyenv#installation and virtualenv
```commandline
pyenv install 3.8.5
pyenv virtualenv 3.8.5 recipes
```
Activate the virtualenv
```commandline
pyenv activate recipes
```
Clone the project
```commandline
git clone git@github.com:PHedro/recipes.git
```
Go to the project folder (the one where you can find the README file)
```commandline
cd /path/to/project/ 
```
Install the project requirements (remember to activate the virtualenv)
```commandline
pip install -r requirements.txt
```

create your database (the system was developed and tested with postgresql)

To run locally you will need to set a .env file using the .env.sample as base on the settings folder.

