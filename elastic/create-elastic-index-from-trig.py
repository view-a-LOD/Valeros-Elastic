import logging
import os
from collections import defaultdict
from typing import Any, Dict, Set

from elasticsearch import Elasticsearch
from rdflib import ConjunctiveGraph, Literal, URIRef

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_USER = os.getenv("ES_USER")
ES_PASSWORD = os.getenv("ES_PASSWORD")
INDEX_NAME = "valeros"
REPLACE_DOTS_WITH_SPACES = os.getenv(
    "REPLACE_DOTS_WITH_SPACES", "false").lower() == "true"


def load_rdf_graph(file_path: str) -> ConjunctiveGraph:
    logger.info(f"Loading RDF data from {file_path}")
    g = ConjunctiveGraph()
    g.parse(file_path, format="trig")
    logger.info(f"Loaded {len(g)} triples")
    return g


def build_documents_from_triples(graph: ConjunctiveGraph) -> Dict[str, Dict[str, Any]]:
    logger.info("Building documents from triples")
    if REPLACE_DOTS_WITH_SPACES:
        logger.info("Dot-to-space replacement is ENABLED for all URIs")
    documents = defaultdict(lambda: {"@id": None})

    for subject, predicate, obj in graph.triples((None, None, None)):
        subject_uri = str(subject)
        predicate_uri = str(predicate)

        if REPLACE_DOTS_WITH_SPACES:
            # subject_uri = subject_uri.replace(".", " ")
            predicate_uri = predicate_uri.replace(".", " ")

        if documents[subject_uri]["@id"] is None:
            documents[subject_uri]["@id"] = subject_uri

        if isinstance(obj, Literal):
            value = obj.toPython()
        elif isinstance(obj, URIRef):
            value = str(obj)
        else:
            value = str(obj)

        # if REPLACE_DOTS_WITH_SPACES and isinstance(value, str):
        #     value = value.replace(".", " ")

        if predicate_uri in documents[subject_uri]:
            if not isinstance(documents[subject_uri][predicate_uri], list):
                documents[subject_uri][predicate_uri] = [
                    documents[subject_uri][predicate_uri]]
            documents[subject_uri][predicate_uri].append(value)
        else:
            documents[subject_uri][predicate_uri] = value

    logger.info(f"Built {len(documents)} documents")
    return dict(documents)


def infer_field_type(values: list) -> str:
    if not values:
        return "text"

    sample = values[0] if isinstance(values, list) else values

    if isinstance(sample, bool):
        return "boolean"
    elif isinstance(sample, int):
        return "long"
    elif isinstance(sample, float):
        return "double"
    else:
        return "text"


def create_dynamic_mapping(documents: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    logger.info("Creating dynamic mapping from document fields")

    all_predicates: Set[str] = set()
    for doc in documents.values():
        all_predicates.update(doc.keys())

    properties = {
        "@id": {
            "type": "text",
            "fields": {
                "keyword": {
                    "type": "keyword",
                    "ignore_above": 256
                }
            }
        }
    }

    for predicate in all_predicates:
        if predicate == "@id":
            continue

        sample_values = []
        for doc in documents.values():
            if predicate in doc:
                sample_values.append(doc[predicate])
                if len(sample_values) >= 10:
                    break

        field_type = infer_field_type(sample_values)

        if field_type == "text":
            properties[predicate] = {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            }
        else:
            properties[predicate] = {"type": field_type}

    mapping = {
        "mappings": {
            "date_detection": False,
            "properties": properties
        }
    }

    logger.info(f"Created mapping with {len(properties)} properties")
    return mapping


def create_index(es: Elasticsearch, index_name: str, mapping: Dict[str, Any]) -> None:
    if es.indices.exists(index=index_name):
        logger.info(f"Deleting existing index: {index_name}")
        es.indices.delete(index=index_name)

    logger.info(f"Creating index: {index_name}")
    es.indices.create(index=index_name, body=mapping)
    logger.info(f"Index {index_name} created successfully")


def index_documents(es: Elasticsearch, index_name: str, documents: Dict[str, Dict[str, Any]]) -> None:
    logger.info(f"Indexing {len(documents)} documents")

    bulk_data = []
    for doc_id, doc in documents.items():
        bulk_data.append({"index": {"_index": index_name, "_id": doc_id}})
        bulk_data.append(doc)

    if bulk_data:
        es.bulk(operations=bulk_data)
        logger.info(f"Successfully indexed {len(documents)} documents")


def main():
    cwd = os.getcwd()
    file_path = os.path.join(cwd, "data.trig")

    graph = load_rdf_graph(file_path)
    documents = build_documents_from_triples(graph)
    mapping = create_dynamic_mapping(documents)

    logger.info(f"Connecting to Elasticsearch at {ES_HOST}")

    es_config = {"hosts": [ES_HOST], "verify_certs": False}
    if ES_USER and ES_PASSWORD:
        es_config["basic_auth"] = (ES_USER, ES_PASSWORD)
        logger.info("Using authentication")
    else:
        logger.info("No authentication configured")

    es = Elasticsearch(**es_config)

    try:
        if not es.ping():
            logger.error("Failed to connect to Elasticsearch")
            return
        logger.info("Connected to Elasticsearch")
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {e}")
        return

    create_index(es, INDEX_NAME, mapping)
    index_documents(es, INDEX_NAME, documents)

    logger.info(
        f"Process complete. Index '{INDEX_NAME}' is ready with {len(documents)} documents")


if __name__ == "__main__":
    main()
