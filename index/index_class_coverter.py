import json
import argparse

class SKGIFConverter:
    def __init__(self):
        self.skgif_context = [
            "https://w3id.org/skg-if/context/skg-if.json",
            {
                "@base": "https://w3id.org/skg-if/sandbox/oc/",
                "skg": "https://w3id.org/skg-if/sandbox/oc/"
            }
        ]

    def convert(self, json_input):
        jsonld_output = {
            "@context": self.skgif_context,
            "@graph": []
        }

        for item in json_input:
            citation_object = {
                "entity_type": "citation",
                "oci": f"oci:{item['oci']}",
                "citing": item["citing"],
                "cited": item["cited"],
                "creation": item["creation"],
                "timespan": item["timespan"],
                "journal_sc": item["journal_sc"],
                "author_sc": item["author_sc"]
            }
            jsonld_output["@graph"].append(citation_object)

        return jsonld_output

def main():
    parser = argparse.ArgumentParser(description="Convert JSON to SKGIF-compliant JSON-LD.")
    parser.add_argument("input_file", help="Path to the input JSON file.")
    parser.add_argument("output_file", help="Path to the output JSON-LD file.")
    args = parser.parse_args()

    with open(args.input_file, 'r') as infile:
        json_input = json.load(infile)

    converter = SKGIFConverter()
    jsonld_output = converter.convert(json_input)

    with open(args.output_file, 'w') as outfile:
        json.dump(jsonld_output, outfile, indent=4)

    print(f"Conversion complete. JSON-LD saved to {args.output_file}")

if __name__ == "__main__":
    main()
