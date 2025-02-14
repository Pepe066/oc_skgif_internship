from json import load, dump
import re
from re import sub
import argparse
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta


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
    
    def create_manifestations_citing(self, datetime_string):
        try:
            dt = datetime.strptime(datetime_string, "%Y-%m-%d")
        except ValueError:
            try:
                dt = datetime.strptime(datetime_string, "%Y-%m")
            except:
                dt = datetime.strptime(datetime_string, "%Y")
        
        return dt.replace(tzinfo=timezone.utc).isoformat()


    def create_manifestations_cited(self, creation_date, timespan): #da rivedere completamente 
        try:
            dt = datetime.strptime(creation_date, "%Y-%m-%d")
        except ValueError:
            try:
                dt = datetime.strptime(creation_date, "%Y-%m")
            except:
                dt = datetime.strptime(creation_date, "%Y")
        

        match = re.match(r"P(\d+)Y(\d+)M(\d+)D", timespan)
        if match:
            years = int(match.group(1))
            months = int(match.group(2))
            days = int(match.group(3))

        publication_date = dt.replace(tzinfo=timezone.utc).isoformat() - relativedelta(years=years, months=months, days=days)
        return [{"dates": {"publication": publication_date.isoformat()}}]

    def create_related_products(self, string):
        for item in string.split():
            if "omid" in item:
                return self.create_omid_url(item)
                

    def convert(self):
        with open(self.json_data, "r", encoding="utf-8") as f:
            oc_json = load(f)

        first_product = oc_json[0]

        citing_product = {
            "local_identifier": self.create_omid_url(first_product["citing"].split()[0]),
            "identifiers": self.create_identifiers(first_product["citing"]),
        }
        if "creation" in first_product:  
            citing_product["manifestations"] = [{ "dates": { "publication" : self.create_manifestations_citing(first_product["creation"])}}]
        citing_product["related_products"] = {"cites" : [self.create_related_products(item["cited"]) for item in oc_json]}

        self.context["@graph"].append(citing_product)
        
        for item in oc_json:

            cited_product = {
                "local_identifier": self.create_omid_url(item["cited"].split()[0]),
                "identifiers": self.create_identifiers(item["cited"]),   
            }
            if "timespan" in item:  
                cited_product["manifestations"] = self.create_manifestations_cited(item["creation"], item["timespan"])

            self.context["@graph"].append(cited_product)

            

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


