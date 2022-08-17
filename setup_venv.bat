python -m venv ./.venv/
cd .venv/Scripts/
python -m pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu113
python -m pip install opencv-python
python -m pip install numpy
python -m pip install pillow
python -m pip install pywin32
cd ../../