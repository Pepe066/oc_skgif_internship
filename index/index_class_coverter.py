from json import load, dump, dumps
from re import sub, findall
from datetime import timezone, datetime
import argparse

class IndexJSONLDConverter:
    def __init__(self, json_data):
        self.base = "https://w3id.org/oc/meta/" 
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
        local_identifier = sub("^.*omid:([^ ]+).*$", self.base + "\\1", string)
        return local_identifier
    def create_identifiers(self, string):
        identifiers = []
        for item in string.split():  
            if ":" in item:
                scheme, value = item.split(":", 1)  
                identifiers.append({"scheme": scheme, "value": value})
        return identifiers
    def create_manifestations(self, string):
        manifestations = []
        manifestations.append({
            "dates": {
                "publication": string + "T00:00:00+00:00"
            }
        })
        return manifestations
    def create_related_products(self, string):
       
        for item in string.split():
            if "omid" in item:
                citation = self.create_omid_url(item)
        return citation
    
    def covert(self):
        with open(self.json_data, "r", encoding="utf-8") as f:
            oc_json = load(f)

            for index, item in enumerate(oc_json[0]):
                if index == 0:
                    citing_product = {
                        "local_identifier" : self.create_omid_url(item["cited"].split()[0]),
                        "identifiers" : self.create_identifiers(item["cited"]),
                        "manifestations" : self.create_manifestations(item["creation"]),
                        "related_products" : {[self.create_related_products(i["cited"]) for i in oc_json]}
                    }
                    product = {
                        "local_identifier" : self.create_omid_url(item["cited"].split()[0]),
                        "identifiers" : self.create_identifiers(item["cited"]),
                        "manifestations" : self.create_manifestations(item["creation"]-item["timespan"]), #da fare con datetime e fare il check se esiste
                    }
                        

    


        
     


    

