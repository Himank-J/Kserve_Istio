import logging
import time
from abc import ABC

import numpy as np
import torch
from diffusers import StableDiffusion3Pipeline
from ts.torch_handler.base_handler import BaseHandler

logger = logging.getLogger(__name__)
logger.info("Loading sd3_handler...")

class SD3Handler(BaseHandler, ABC):
    def __init__(self):
        self.initialized = False
        logger.info("Initializing SD3Handler...")

    def initialize(self, ctx):
        """Initialize the model. The model is loaded from the mounted PVC path."""
        start_time = time.time()
        logger.info("Starting initialization...")

        self.manifest = ctx.manifest
        properties = ctx.system_properties

        # Print all system properties
        logger.info("System Properties:")
        for key, value in properties.items():
            logger.info(f"  {key}: {value}")

        model_dir = properties.get("model_dir")

        # KServe mounts the model files at /mnt/models
        model_dir = (
            "/mnt/models/sd3-model"  # Point to where KServe mounts the model weights
        )

        logger.info(f"Using model directory: {model_dir}")

        # Set up device
        self.device = torch.device(
            "cuda:" + str(properties.get("gpu_id"))
            if torch.cuda.is_available() and properties.get("gpu_id") is not None
            else "cpu"
        )
        logger.info(f"Using device: {self.device}")

        # Log GPU info
        if torch.cuda.is_available():
            logger.info(
                f"GPU Memory before loading: {torch.cuda.memory_allocated()/1e9:.2f}GB"
            )

        # Load model directly from the mounted path
        try:
            logger.info("Loading SD3 pipeline...")
            self.pipe = StableDiffusion3Pipeline.from_pretrained(
                model_dir, torch_dtype=torch.bfloat16
            )
            self.pipe = self.pipe.to(self.device)
            logger.info("Pipeline loaded and moved to device successfully")
        except Exception as e:
            logger.error(f"Error during pipeline loading: {str(e)}")
            raise

        if torch.cuda.is_available():
            logger.info(
                f"GPU Memory after loading: {torch.cuda.memory_allocated()/1e9:.2f}GB"
            )

        self.initialized = True
        end_time = time.time()
        logger.info(f"Initialization completed in {end_time - start_time:.2f} seconds")

    def preprocess(self, requests):
        """Process the input prompt."""
        logger.info("Starting preprocessing...")
        inputs = []
        for idx, data in enumerate(requests):
            input_text = data.get("data")
            if input_text is None:
                input_text = data.get("body")
            if isinstance(input_text, (bytes, bytearray)):
                input_text = input_text.decode("utf-8")
            inputs.append(input_text)
        return inputs

    def inference(self, inputs):
        """Generate the image from the prompt."""
        logger.info(f"Starting inference with {len(inputs)} inputs")
        start_time = time.time()

        try:
            inferences = self.pipe(
                inputs,
                num_inference_steps=28,
                guidance_scale=7.0,
                width=1024,
                height=1024,
            ).images

            if torch.cuda.is_available():
                logger.info(
                    f"GPU Memory after inference: {torch.cuda.memory_allocated()/1e9:.2f}GB"
                )

        except Exception as e:
            logger.error(f"Error during inference: {str(e)}")
            raise

        end_time = time.time()
        logger.info(f"Inference completed in {end_time - start_time:.2f} seconds")
        return inferences

    def postprocess(self, inference_output):
        """Convert the generated images to the required format."""
        logger.info("Starting postprocessing...")
        images = []
        for image in inference_output:
            images.append(np.array(image).tolist())
        return images