from json import load, dump
from re import sub
import argparse
from datetime import datetime, timezone

class IndexJSONLDConverter:
    def __init__(self, json_data):
        self.base = "https://w3id.org/oc/index/"
        self.json_data = json_data

        self.context = {
            "@context": [
                "https://w3id.org/skg-if/context/skg-if.json",
                {
                    "@base": "https://w3id.org/skg-if/sandbox/oc/",
                    "skg": "https://w3id.org/skg-if/sandbox/oc/"
                }
            ],
            "@graph": []
        }

    def create_omid_url(self, string):
        return sub(r"^.*omid:([^ ]+).*$", self.base + r"\1", string)

    def create_identifiers(self, string):
        identifiers = []
        for item in string.split():
            if ":" in item:
                scheme, value = item.split(":", 1)
                identifiers.append({"scheme": scheme, "value": value})
        return identifiers

    def create_manifestations(self, creation_date, timespan=None):
        try:
            creation_dt = datetime.fromisoformat(creation_date).replace(tzinfo=timezone.utc)
            if timespan:
                timespan_dt = datetime.fromisoformat(timespan).replace(tzinfo=timezone.utc)
                publication_date = (creation_dt - timespan_dt).isoformat()
            else:
                publication_date = creation_dt.isoformat()
        except ValueError:
            publication_date = creation_date + "T00:00:00+00:00"

        return [{"dates": {"publication": publication_date}}]

    def create_related_products(self, string):
        citations = []
        for item in string.split():
            if "omid" in item:
                citations.append(self.create_omid_url(item))
        return citations

    def convert(self):
        with open(self.json_data, "r", encoding="utf-8") as f:
            oc_json = load(f)

        # Remove the [0] since we don't have the extra nesting level
        for item in oc_json:
            citing_product = {
                "local_identifier": self.create_omid_url(item["citing"].split()[0]),
                "identifiers": self.create_identifiers(item["citing"]),
                "manifestations": self.create_manifestations(item["creation"]),
                "related_products": self.create_related_products(item["citing"])
            }

            cited_product = {
                "local_identifier": self.create_omid_url(item["cited"].split()[0]),
                "identifiers": self.create_identifiers(item["cited"]),
                "manifestations": self.create_manifestations(item["creation"], item.get("timespan"))
            }

            self.context["@graph"].extend([citing_product, cited_product])

    def save(self, output_file):
        with open(output_file, "w", encoding="utf-8") as f:
            dump(self.context, f, indent=2, ensure_ascii=False)

# Usage

def main():
    parser = argparse.ArgumentParser(description="Convert JSON to JSON-LD format")
    parser.add_argument("input_file", help="Path to the JSON input file")
    parser.add_argument("output_file", help="Path to save the JSON-LD output file")
    args = parser.parse_args()

    converter = IndexJSONLDConverter(args.input_file)
    converter.convert()
    converter.save(args.output_file)

    print(f"JSON-LD saved to {args.output_file}")

if __name__ == "__main__":
    main()


