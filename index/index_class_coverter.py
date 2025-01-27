import json
import argparse

class IndexJSONLDConverter:
    def __init__(self):
        self.skgif_context = [
            "https://w3id.org/skg-if/context/skg-if.json",
            {
                "@base": "https://w3id.org/skg-if/sandbox/oc/",
                "skg": "https://w3id.org/skg-if/sandbox/oc/"
            }
        ]
    def convert(self, input_json, base="https://w3id.org/oc/meta/"):
        self.input_data = input_json
        self.base = base
        self.result = {
            "@context": self.skgif_context,
            "@graph": []
        }
    

