## BiTory

All processes run on the Streamlit web browser interface. 
A microphone may be required for voice cloning and vocal interaction with the system.

### Before you start
As specified in `.gitignore`, the `.env` file is intentionally excluded from the repository.
You need to create this file and add your own `OPENAI_API_KEY` from your OpenAI account to use the GPT-4 and DALL·E 3 models, which are essential for this system.

You will also need CoquiAI's `xtts_v2.0.2` model.
Since the model file is too large to upload to the repository, you must download and install it locally, then move the files to this directory.
We store the model files in a folder named `xtts` located in the parent directory of the project.
The folder should contain the following files:
`config.json`, `hash.md5`, `model.pth`, `speakers_xtts.pth`, `tos_agreed.txt`, and `vocab.json`.


```python
# Download xtts_v2.0.2 (use this version instead of v2.0.3 if your main use case involves non-English speech)
# Identify the default directory where the model is installed
# IMPORTANT: The default directory may be a hidden folder (e.g., C:\Users\YOUR_NAME\AppData\... on Windows OS)
from TTS.api import TTS
TTS("xtts_v2.0.2", gpu=False)

# Move the downloaded files from the default directory to your working directory
!mv [DEFAULT_DIR]/tts_models--multilingual--multi-dataset--xtts_v2.0.2/* [YOUR_WORKING_DIR]/tts/
```

### Run
After setting up the `xtts` folder and `.env` file, you can start the application by running:\
```streamlit run cover_page.py --client.showSidebarNavigation=False -- ```

### Argparse options
- Use GPU: `--use_gpu`
- Upload your own pre-recorded voices: `--uv`
