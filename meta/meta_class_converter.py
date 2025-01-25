from json import load, dump, dumps
from re import sub, findall
from datetime import timezone, datetime
import argparse

class JSONLDConverter:
    def __init__(self, input_json, base="https://w3id.org/oc/meta/"):
        self.input_data = input_json
        self.base = base
        self.type_mapping = {
            "journal article": "http://purl.org/spar/fabio/JournalArticle",
            "book chapter": "http://purl.org/spar/fabio/BookChapter"
        }
        self.venue_mapping = {
            "journal article": "journal",
            "book chapter": "book"
        }
        self.result = {
            "@context": [
                "https://w3id.org/skg-if/context/skg-if.json",
                {
                    "@base": "https://w3id.org/skg-if/sandbox/oc/",
                    "skg": "https://w3id.org/skg-if/sandbox/oc/"
                }
            ],
            "@graph": []
        }

    def get_datetime(self, datetime_string):
        formats = ["%Y-%m-%d", "%Y-%m", "%Y"]
        for fmt in formats:
            try:
                dt = datetime.strptime(datetime_string, fmt)
                return dt.replace(tzinfo=timezone.utc).isoformat()
            except ValueError:
                continue
        return None

    def get_omid_url(self, string):
        return sub("^.*omid:([^ ]+).*$", self.base + "\\1", string)

    def create_identifiers(self, identifiers, entity):
        for identifier in identifiers.split(" "):
            if "identifiers" not in entity:
                entity["identifiers"] = []
            scheme, value = identifier.split(":", 1)
            entity["identifiers"].append({
                "scheme": scheme,
                "value": value
            })

    def create_contributors(self, contributor_list, contributor_type):
        contributors = []
        agents = []
        contributor_rank = 0

        for contributor in contributor_list:
            if contributor != "":
                contributor_rank += 1
                name, ids = findall("^(.+) \\[(.+)\\]$", contributor)[0]
                contributor_omid = self.get_omid_url(ids)

                contributor_object = {
                    "by": contributor_omid,
                    "role": contributor_type
                }

                if contributor_type != "publisher":
                    contributor_object["rank"] = contributor_rank

                contributors.append(contributor_object)

                agent_object = {"local_identifier": contributor_omid}
                self.create_identifiers(ids, agent_object)

                if ", " in name:
                    agent_object["entity_type"] = "person"
                    fn, gn = name.split(", ")
                    if gn:
                        agent_object["given_name"] = gn
                    if fn:
                        agent_object["family_name"] = fn
                else:
                    agent_object["entity_type"] = "organisation" if contributor_type == "publisher" else "agent"
                    if name:
                        agent_object["name"] = name

                agents.append(agent_object)

        return contributors, agents

    def process_item(self, item):
        g = self.result["@graph"]
        research_product = {"entity_type": "product"}
        g.append(research_product)

        research_product["local_identifier"] = self.get_omid_url(item["id"])
        self.create_identifiers(item["id"], research_product)

        if item["type"] in ("data file", "dataset"):
            research_product["product_type"] = "research data"
        elif item["type"] == "software":
            research_product["product_type"] = "research software"
        else:
            research_product["product_type"] = "literature"

        if "title" in item and item["title"] != "":
            research_product["titles"] = {"none": item["title"]}

        authors, author_agents = self.create_contributors(item["author"].split("; "), "author")
        editors, editor_agents = self.create_contributors(item["editor"].split("; "), "editor")
        publishers, publisher_agents = self.create_contributors(item["publisher"].split("; "), "publisher")

        research_product["contributions"] = authors + editors + publishers
        g.extend([agent for agent in author_agents + editor_agents + publisher_agents if agent not in g])

        manifestation = {
            "type": {
                "class": self.type_mapping[item["type"]],
                "labels": {"en": item["type"]},
                "defined_in": "http://purl.org/spar/fabio"
            }
        }

        self.create_identifiers(item["id"], manifestation)

        if item["pub_date"] != "":
            manifestation["dates"] = {"publication": self.get_datetime(item["pub_date"])}

        if any([item["volume"], item["page"], item["venue"], item["issue"]]):
            manifestation["biblio"] = {}

            if item["issue"] != "":
                manifestation["biblio"]["issue"] = item["issue"]
            if item["volume"] != "":
                manifestation["biblio"]["volume"] = item["volume"]
            if item["page"] != "":
                sp, ep = item["page"].split("-")
                manifestation["biblio"]["pages"] = {"first": sp, "last": ep}
            if item["venue"] != "":
                name, ids = findall("^(.+) \\[(.+)\\]$", item["venue"])[0]
                venue_omid = self.get_omid_url(ids)
                manifestation["biblio"]["in"] = venue_omid

                venue_object = {
                    "local_identifier": venue_omid,
                    "entity_type": "venue",
                    "title": name,
                    "type": self.venue_mapping[item["type"]]
                }

                self.create_identifiers(ids, venue_object)

                if len(editors) and self.venue_mapping[item["type"]] == "book":
                    venue_object.setdefault("contributions", []).extend(editors)
                if len(publishers):
                    venue_object.setdefault("contributions", []).extend(publishers)

                g.append(venue_object)

        research_product["manifestations"] = [manifestation]

    def convert(self):
        for item in self.input_data:
            self.process_item(item)
        return self.result

    def save_to_file(self, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            dump(self.result, f, ensure_ascii=False, indent=4)

    def get_jsonld(self):
        return dumps(self.result, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='JSON OCDM API format to JSON-LD SKG-IF converter')
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        input_json = load(f)

    converter = JSONLDConverter(input_json)
    converter.convert()
    converter.save_to_file(args.output)
    print(converter.get_jsonld())
