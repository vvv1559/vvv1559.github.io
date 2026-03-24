## Prepare
```shell
cd /Users/vlad/Documents/vvv1559.github.io
brew install weasyprint
python3 -m venv .venv
source venv/bin/activate
pip install -r source/requirements.txt
```

## Generate
```shell
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH
python3 source/generator.py
```