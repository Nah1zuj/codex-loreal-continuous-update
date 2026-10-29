# ASR model files

The large `model.int8.onnx` file is intentionally not stored in this GitHub
repository because it exceeds GitHub's 100 MB single-file limit. Keep a local
copy in this directory, or download the official export with:

```bash
python voice/setup_local_voice_models.py
```

Run that command from the `AccessibleBeautyAgent` directory. The setup scripts
also download missing local speech models during first-time installation.

This directory contains models converted from
https://github.com/FunAudioLLM/SenseVoice. Keep the accompanying license and
model source notices with the model files.
