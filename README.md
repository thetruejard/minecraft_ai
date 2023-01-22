# Minecraft AI
A simple PyTorch framework for training an AI to play [Minecraft](https://www.minecraft.net/en-us).

**This project is effectively a sandbox for my personal use.** Feel free to use it (subject to the license below), submit issues, etc., but I cannot promise it will work for any particular purpose.

# Usage

1. To create a new model, run:
   ```
   python . create dest/path/
   ```
   Where `dest/path/` is the path where the model will be saved.

2. Open a Minecraft world and pause the game. This framework targets Java Edition, but other editions may work too.

3. To start the model, run:
   ```
   python . run model/path/
   ```
   Where `model/path/` is the path to the model created in step 1. To run it without training, specify `--no_train` or `-nt`.
   
# Dependencies

See `setup_venv.bat` for a list of dependencies as `pip` installs.

Note that this project currently only supports Windows. See Limitations below.

# Customization

The provided design in `master` is a simple vision-based model that only controls the camera rotation, with the look of "look at the pig". That is, it attempts to rotate the player's head to look at the nearest pink object. More advanced designs may replace this in `master` as they are developed.

The framework has a generalized structure that supports training for a wide variety of tasks.

## Processes

Each "Process" runs in parallel using python's built-in multiprocessing. This allows multiple sub-tasks to run simultaneously.

The provided "look at the pig" design comes with 4 processes:
- `vision.ScreenGrab`: repeatedly grab the screen, providing a video input feed
- `vision.VisionProcessing`: preprocess the video input feed
- `SimpleLogic`: a simple machine learning-based logical process, trained in realtime
- `Controls`: takes inputs specifying movement controls and sends them to the Minecraft instance

See `process.py` for the base class, and the above classes for example implementations.

## Models

A Model is a PyTorch Module attached to a Process. Each Process can have multiple Models attached to it, and they are matched by name and type upon loading.

See `simplelogic.py` for an example.

## Creation

`create()` in `__main__.py` specifies how Processes connect and interact.

See the implementation in `master` for an example.

## Connection Policies

There are 2 policies for how connections between processes are handled:
1. Discrete: The receiving Process waits until *new* input is available, blocking if necessary.
2. Continuous: The receiving Process uses the most recently available input, regardless of whether it's new or old.

# Limitations

This project is still in the early stages of development. There are significant limitations:

- Currently only Windows is supported (via pywin32). Currently, abstractions are used to make supporting other platforms easy, but there are no implementations yet.
- **The Process implementations must be the same when creating and running.** This is a design decision that may or may not be readdressed. If a modification is made to a Process, any old models using that Process may or may not continue to work.
- Keyboard input is untested. This is a current development focus.

# License

If you can find a use for this code, by all means go ahead. Credit is appreciated but not necessary. The only limitation is no commercial use. Do not sell this code, any derivative code, or any models or products produced with this code or derivative code.

This project is in no way affiliated with [Minecraft](https://www.minecraft.net/en-us).
