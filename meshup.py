import requests
import argparse
from json import load, dump
from meta.meta_class_converter import MetaClassConverter
from index.index_class_coverter import IndexClassConverter


class IndexMetaMeshup:
    def __init__(self, doi):
        self.doi = doi  
        self.meta_base_url = "https://w3id.org/oc/meta/api/v1"
        self.index_base_url = "https://opencitations.net/index/api/v1"
        self.index_class_converter = IndexClassConverter()
        self.meta_class_converter = MetaClassConverter()
    
    def get_citations(self, doi):  
        doi_encoded = requests.utils.quote(doi)
        url = f"{self.index_base_url}/citations/{doi_encoded}"  
        response = requests.get(url)

        if response.status_code == 200:
            idex_jsonld = self.index_class_converter.convert(response.json())
            return  idex_jsonld
        else:
            print(f"Error: {response.status_code}")
            return None
        
    def get_metadata(self, idex_jsonld):  
        index_dois = []
        url = f"{self.meta_base_url}/metadata/{'__'.join(index_dois)}"  #

        doi_date_dict = {}
        for product in idex_jsonld["@graph"]:
            if "identifiers" in product:
                for identifier in product["identifiers"]:
                    if identifier["scheme"] == "doi":
                        index_dois.append(identifier["value"])

                    if "manifestations" in product:
                        for manifestation in product["manifestations"]:
                            if "dates" in manifestation and "publication" in manifestation["dates"]:
                                publication_date = manifestation["dates"]["publication"]
                                doi_date_dict[product["local_identifier"]] = publication_date
            
        response = requests.get(url)
        if response.status_code == 200:
            meta_jsonld = self.meta_class_converter.convert(response.json())
            for product in meta_jsonld["@graph"]:
                if "manifestations" in product:
                    for manifestation in product["manifestations"]:
                        if "dates" in manifestation and "publication" in manifestation["dates"]:
                            if manifestation["dates"] != doi_date_dict[product["local_identifier"]]:
                                manifestation["dates"] = manifestation["dates"]

            return meta_jsonld
        else:
            print(f"Error: {response.status_code}")
            return None
        
    def save(self, output_file):
        with open(output_file, "w", encoding="utf-8") as f:
            dump(self.context, f, indent=2, ensure_ascii=False)
        
def main():
    parser = argparse.ArgumentParser(description="Convert JSON to JSON-LD format")
    parser.add_argument("doi", help="Insert the DOI to get metadata")
    parser.add_argument("output_file", help="Path to save the JSON-LD output file")
    args = parser.parse_args()

    index_meta = IndexMetaMeshup(args.doi)

    # Get citations
    idex_jsonld = index_meta.get_citations(args.doi)
    if not idex_jsonld:
        print("Failed to fetch citations.")
        return

    # Get metadata
    meta_jsonld = index_meta.get_metadata(idex_jsonld)
    if not meta_jsonld:
        print("Failed to fetch metadata.")
        return

    # Save the JSON-LD output
    index_meta.save(args.output_file)
    print(f"JSON-LD saved to {args.output_file}")

if __name__ == "__main__":
    main()





