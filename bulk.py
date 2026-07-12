"""
Bulk copy generation from a CSV file.
Uses asyncio + httpx.AsyncClient to send several requests to Ollama
at the same time, with a Semaphore capping how many run concurrently.
 
Usage:
    python bulk.py --input products.csv --output results.csv --concurrency 3
 
products.csv columns: product_name,platform,tone,description
"""
 
import asyncio
import csv
import time
import argparse
import httpx
from main import build_master_prompt, MarketingCopy, clean_ai_intro, compact_for_csv
 
OLLAMA_URL = "http://localhost:11434/api/chat"
 
 
async def generate_copy_async(prompt: str, client: httpx.AsyncClient, semaphore: asyncio.Semaphore,
                               temperature=0.7, top_p=0.9) -> str:
    async with semaphore:
        payload = {
            "model": "llama3",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": temperature, "top_p": top_p}
        }
        response = await client.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()["message"]["content"]
 
 
async def process_one_row(row: dict, client: httpx.AsyncClient, semaphore: asyncio.Semaphore) -> dict:
    prompt = build_master_prompt(
        product_name=row["product_name"],
        platform=row["platform"],
        tone=row["tone"],
        raw_description=row["description"]
    )
 
    try:
        copy_text = await generate_copy_async(prompt, client, semaphore)
        copy_text = clean_ai_intro(copy_text)
        validated = MarketingCopy(
            product_name=row["product_name"],
            platform=row["platform"],
            tone=row["tone"],
            copy_text=copy_text
        )
        return {
            "product_name": row["product_name"],
            "platform": row["platform"],
            "tone": row["tone"],
            "generated_copy": compact_for_csv(validated.copy_text),
            "status": "success"
        }
    except Exception as e:
        return {
            "product_name": row["product_name"],
            "platform": row["platform"],
            "tone": row["tone"],
            "generated_copy": "",
            "status": f"failed: {e}"
        }
 
 
async def run_bulk(input_csv: str, output_csv: str, concurrency: int):
    with open(input_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
 
    print(f"[INFO] {len(rows)} products found. Concurrency limit: {concurrency}")
 
    semaphore = asyncio.Semaphore(concurrency)
    start_time = time.time()
 
    async with httpx.AsyncClient() as client:
        tasks = [process_one_row(row, client, semaphore) for row in rows]
        results = await asyncio.gather(*tasks)
 
    elapsed = time.time() - start_time
 
    # utf-8-sig so emojis render correctly when opened in Excel
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["product_name", "platform", "tone", "generated_copy", "status"])
        writer.writeheader()
        writer.writerows(results)
 
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"[DONE] {success_count}/{len(rows)} successful. Took {elapsed:.1f}s")
    print(f"[SAVED] Results written to '{output_csv}'.")
 
 
def main():
    parser = argparse.ArgumentParser(description="Bulk copy generation from a CSV file")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="results.csv")
    parser.add_argument("--concurrency", type=int, default=3)
 
    args = parser.parse_args()
    asyncio.run(run_bulk(args.input, args.output, args.concurrency))
 
 
if __name__ == "__main__":
    main()
 