import asyncio
import time
import csv
import matplotlib.pyplot as plt
from unoserver.client import UnoClient
import logging

# Configuration
UNOSERVER_HOST = "remote"  # Replace with your Unoserver host
UNOSERVER_PORT = 2003  # Replace with your Unoserver port
DOCX_FILE = "test.docx"
CONCURRENCY_LEVEL = 50  # Number of concurrent requests
TOTAL_REQUESTS = 500  # Total requests to send

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize UnoClient
client = UnoClient(port=UNOSERVER_PORT, host_location=UNOSERVER_HOST)

# Function to convert DOCX to PDF
async def convert_to_pdf(input_data: bytes) -> dict:
    try:
        logger.debug("Starting conversion...")
        start_time = time.monotonic()
        outdata = client.convert(indata=input_data, convert_to="pdf")
        latency = time.monotonic() - start_time
        if outdata:
            return {"status": "success", "latency": latency}
        else:
            return {"status": "empty_response", "latency": latency}
    except Exception as e:
        latency = time.monotonic() - start_time
        return {"status": "exception", "latency": latency, "error": str(e)}

# Load test function
async def load_test():
    results = []
    tasks = []

    # Load the DOCX file into memory once
    with open(DOCX_FILE, "rb") as f:
        file_data = f.read()

    for _ in range(TOTAL_REQUESTS):
        tasks.append(convert_to_pdf(file_data))
        if len(tasks) == CONCURRENCY_LEVEL:
            results.extend(await asyncio.gather(*tasks))
            tasks = []
    if tasks:  # Handle remaining tasks
        results.extend(await asyncio.gather(*tasks))
    return results

# Save results to CSV
def save_results_to_csv(results, filename="load_test_results.csv"):
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Status", "Latency (s)", "Error"])
        for result in results:
            writer.writerow([result["status"], result["latency"], result.get("error", "")])

# Generate graphs
def generate_graph(results):
    latencies = [r["latency"] for r in results if r["status"] == "success"]
    error_count = sum(1 for r in results if r["status"] != "success")

    # Latency Histogram
    plt.figure(figsize=(10, 6))
    plt.hist(latencies, bins=30, edgecolor="k")
    plt.title("Latency Distribution")
    plt.xlabel("Latency (s)")
    plt.ylabel("Frequency")
    plt.savefig("latency_histogram.png")

    # Error Count
    plt.figure(figsize=(10, 6))
    plt.bar(["Success", "Error"], [len(latencies), error_count])
    plt.title("Success vs Error Count")
    plt.ylabel("Count")
    plt.savefig("success_vs_error.png")

async def main():
    print("Starting load test...")
    results = await load_test()
    print("Load test completed. Saving results...")
    save_results_to_csv(results)
    print("Generating graphs...")
    generate_graph(results)
    print("Graphs saved. Test complete.")

if __name__ == "__main__":
    asyncio.run(main())
