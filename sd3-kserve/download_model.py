#!/usr/bin/env python3

import torch
from diffusers import StableDiffusion3Pipeline
import os

os.environ["HUGGING_FACE_HUB_TOKEN"] = "<token_here>"

def main():
    print("Downloading SD3 model...")

    # Create output directory
    os.makedirs("sd3-model", exist_ok=True)

    # Download and save model
    pipe = StableDiffusion3Pipeline.from_pretrained(
        "stabilityai/stable-diffusion-3-medium-diffusers", torch_dtype=torch.bfloat16
    )

    print("Saving model to disk...")
    pipe.save_pretrained("./sd3-model")
    print("Model downloaded and saved successfully!")

if __name__ == "__main__":
    main()