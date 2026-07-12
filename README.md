# Automated Copywriting & Tone Transformer
A Python application that generates platform-specific marketing copy using AI. Simply provide a product name, platform, tone, and description, and the tool creates ready-to-use promotional content tailored for the selected platform.

This project was developed as **Project 2** during the **DecodeLabs Generative AI Internship**.

## Features
- Generate marketing copy for LinkedIn, Instagram, and Email
- Support for different writing tones (Professional, Friendly, Casual, etc.)
- Automatic fallback between Claude, Gemini, and Ollama
- Adjustable Temperature and Top_P settings for creativity control
- Automatic retry for failed API requests using Tenacity
- Output validation using Pydantic
- Bulk copy generation from a CSV file using asyncio and httpx

## Tech Stack
- Python
- Anthropic Claude API
- Google Gemini API
- Ollama
- Pydantic
- Tenacity
- asyncio
- httpx

## Installation
Install the required packages:

```bash
pip install -r requirements.txt
```

Set the following environment variables:
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`

(Optional) Install Ollama for local fallback:
```bash
ollama pull llama3
```

## Usage
Generate copy for a single product:

```bash
python main.py --product "Comfy Running Shoes" --platform linkedin --tone professional --description "Lightweight running shoes with extra cushion"
```

Generate marketing copy for multiple products from a CSV file:
```bash
python bulk.py --input products.csv --output results.csv
```
The input CSV file should contain the following columns:

- `product_name`
- `platform`
- `tone`
- `description`

## Project Structure
```text
main.py
bulk.py
requirements.txt
README.md
```

## Notes
- The project automatically switches between Claude, Gemini, and Ollama if a provider is unavailable.
- Bulk processing is implemented using `asyncio` and `httpx` for efficient concurrent requests.
- Ollama serves as a local fallback model and may produce slightly different results compared to cloud-based models.
