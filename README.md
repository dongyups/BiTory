## BiTory

All procedures are run on the Streamlit web browser interface. You may need a microphone for voice cloning and vocal interaction with the system.

### Before you start
According to gitignore, you may see ".env" file is intentionally omitted.
You have to fill the file with your own OPENAI_API_KEY from your OPENAI account in order to use GPT-4 and DALL-E 3 models which are essential for the system.

You also have to prepare CoquiAI's "xtts_v2.0.2" model.
Since the file size is too big to upload, you have to install the model on your local computer and move the files into this directory. We store the model in the "xtts" folder in this parent directory. You may find the following component files of xtts: config.json, hash.md5, model.pth, speakers_xtts.pth, tos_agreed.txt, vocab.json

```python
# download xtts_v2.0.2 (not v2.0.3 if you mainly utilize the model for non-English speech) and figure out the default directory where the model is installed
# IMPORTANT: the default directory can be a hidden folder e.g.) C:\Users\USER_NANE\AppData\... for Windows OS
from TTS.api import TTS
TTS("xtts_v2.0.2", gpu=False)

# move it from the default download folder to your working directory
!mv [DEFAULT_DIR]/tts_models--multilingual--multi-dataset--xtts_v2.0.2/* [YOUR_WORKING_DIR]/tts/
```

### Run
After successfully preparing "xtts" and ".env", run as below.
Run ```streamlit run cover_page.py -- ```

Argparse options.
- using gpu: --use_gpu
- upload your own prepared voices: --uv
