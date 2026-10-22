from urllib.request import urlopen
from zipfile import ZipFile
from io import BytesIO
import csv

url = "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_supplemented.zip"

response = urlopen(url)
data = response.read()

print("Downloaded:", len(data), "bytes")

with ZipFile(BytesIO(data)) as z:
    with z.open("stops.txt") as f:
        reader = csv.DictReader(
            line.decode("utf-8") for line in f
        )

        for row in reader:
            if "4 Av" in row["stop_name"] or "4th Av" in row["stop_name"]:
                print(
                    "Stop ID:",
                    row["stop_id"],
                    "| Name:",
                    row["stop_name"],
                    "| Parent:",
                    row["parent_station"]
                )
