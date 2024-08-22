eval "$(pyenv init -)"
pyenv activate sosia
pytest --cov=sosia --verbose 