import requests
import json
import numpy as np
from PIL import Image
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_image(prompt: str, output_path: str = "output.jpg"):
    """
    Generate an image using the local TorchServe SD3 model.
    Args:
        prompt (str): The text prompt for image generation
        output_path (str): Path where the generated image will be saved
    """
    # Endpoint configuration
    url = "http://k8s-istioing-istioing-163c0111d9-c1e5608c48727220.elb.ap-south-1.amazonaws.com/v1/models/sd3:predict"

    # Headers
    headers = {
        "Host": "torchserve-sd3-default.example.com",
        "Content-Type": "application/json",
    }

    # Format payload according to handler's expectations
    payload = {"instances": [{"data": prompt}]}

    try:
        # Make the request
        logger.info(f"Sending request to {url} with prompt: {prompt}")
        response = requests.post(
            url,
            json=payload,  # Use json parameter to properly serialize
            headers=headers,
        )

        # Check if request was successful
        response.raise_for_status()

        # Convert response to image
        logger.info("Converting response to image")
        image_array = np.array(response.json()["predictions"][0], dtype="uint8")
        image = Image.fromarray(image_array)

        # Save the image
        logger.info(f"Saving image to {output_path}")
        image.save(output_path)
        logger.info("Image generation completed successfully")

        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Error making request: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response text: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Error processing response: {str(e)}")
        return False

def list_models():
    base_url = "http://k8s-istioing-istioing-163c0111d9-c1e5608c48727220.elb.ap-south-1.amazonaws.com"
    headers = {
        "Host": "torchserve-sd3-default.example.com",
    }

    v1_url = f"{base_url}/v1/models"

    try:
        v1_response = requests.get(v1_url, headers=headers)
        print("V1 Models:", v1_response.text)
    except Exception as e:
        print("Error getting v1 models:", str(e))

if __name__ == "__main__":
    # List available models first
    # list_models()

    # Test prompts
    prompts = [
        # "Poster with a gamer in year 2050",
        "Spider-man in Avengers",
        # "a magical forest with glowing mushrooms at night",
        # "Tiger and Lion playing chess",
        # "Ronaldo and Messi playing basketball"
    ]

    # Generate images for each prompt
    for i, prompt in enumerate(prompts):
        output_path = f"output_{i+1}.jpg"
        logger.info(f"\\nGenerating image {i+1} of {len(prompts)}")
        success = generate_image(prompt, output_path)
        if success:
            logger.info(f"Successfully generated {output_path}")
        else:
            logger.error(f"Failed to generate {output_path}")