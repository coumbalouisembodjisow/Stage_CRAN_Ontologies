from owlready2 import *
import json

def load_all_dependencies():
    deps = [
        "onto/ssn.rdf",
        "onto/sosa.rdf",
        "onto/SysAgent.owl",
        "onto/CognitionOnto.owl",
        "onto/SOMA.owl",
        "onto/DUL.owl",
        "onto/AI4C2PS-core.owl"
    ]
    return [get_ontology(f"file://{path}").load() for path in deps]

# Extraire les namespaces des classes instanciées et des propriétés
def generate_ngsi_ld_context(onto):
    context = {
        "@context": [
            "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.jsonld",
            "https://schema.lab.fiware.org/ld/context"
        ]
    }

    # Parcours des classes de l'ontologie, mais uniquement celles ayant des instances
    for cls in onto.classes():
        # Si la classe a des instances, on l'ajoute au contexte
        if len(cls.instances()) > 0:  # La classe a des individus instanciés
            ns = cls.iri.split("#")[0]  # Extrait le namespace à partir de l'IRI de la classe
            context["@context"].append({cls.name : ns})

    # Ajouter les propriétés de l'ontologie au contexte
    for prop in onto.object_properties() :
        ns = prop.iri.split("#")[0]  # Extrait le namespace de la propriété
        context["@context"].append({prop.name: ns})
    for prop in onto.data_properties():
        ns = prop.iri.split("#")[0]
        context["@context"].append({prop.name: ns})
        
    return context
def get_first_declared_class(inst):
    """Récupère la première classe déclarée dans le fichier OWL"""
    # Accès direct à la déclaration RDF de l'instance
    rdf_type = inst.is_a[0] if inst.is_a else None
    
    # Si c'est une classe simple, on la retourne
    if isinstance(rdf_type, ThingClass):
        return rdf_type.name
    
    # Si c'est une restriction OWL, on cherche le type réel
    if hasattr(rdf_type, 'property') and hasattr(rdf_type, 'value'):
        # Cas particulier : restrictions de type
        if rdf_type.property == onto_main.type:
            return rdf_type.value.name
    
    # Parcours des triplets RDF pour trouver le premier rdf:type
    for triple in onto_main.world.triples((inst.iri, None, None)):
        if triple[1] == onto_main.world._rdf_type:
            if isinstance(triple[2], ThingClass):
                return triple[2].name
    return "Entity"
# Enregistrer l'état pré-raisonnement des individus
def record_pre_reasoning_state(onto):
    state = {}
    for inst in onto.individuals():
        # Capture les classes directes
        classes = {cls for cls in inst.is_a if isinstance(cls, ThingClass)}
        
        # Capture les propriétés
        obj_props = {}
        for prop in onto.object_properties():
            obj_props[prop] = set(prop[inst])
        
        data_props = {}
        for prop in onto.data_properties():
            data_props[prop] = set(prop[inst])
        
        state[inst] = {
            "classes": classes,
            "object_properties": obj_props,
            "data_properties": data_props
        }
    return state

def iri_to_ngsi_ld(inst):
    """Génère un IRI NGSI-LD avec le premier type déclaré"""
    class_name = get_first_declared_class(inst)
    return f"urn:ngsi-ld:{class_name}:{inst.name}"

def extract_ontology_to_ngsi_ld(onto, context):
    sync_reasoner([onto], infer_property_values=True, ignore_unsupported_datatypes=True)

    entities = []
    rules = []

    for inst in onto.individuals():
        classes = [cls.name for cls in inst.is_a if isinstance(cls, ThingClass)]
        if not classes:
            continue
        main_class = classes[0]
        entity = {
            "id": iri_to_ngsi_ld(inst),
            "type": list(set(cls.name for cls in inst.is_a if isinstance(cls, ThingClass))),
            "name": inst.name
        }

        for prop in onto.object_properties():
            values = list(prop[inst])
            if values:
                objects = [iri_to_ngsi_ld(v) for v in values]
                entity[prop.name] = {
                    "type": "Relationship",
                    "object": objects[0] if len(objects) == 1 else objects
                }

        for prop in onto.data_properties():
            values = list(prop[inst])
            if values:
                entity[prop.name] = {
                    "type": "Property",
                    "value": values[0] if len(values) == 1 else values
                }

        entities.append(entity)

    for rule in onto.rules():
        try:
            rule_name = rule.name if rule.name else f"Rule_{abs(hash(rule))}"
            rules.append({
                "id": f"urn:ngsi-ld:Rule:{rule_name}",
                "type": "SWRLRule",
                "value": str(rule)
            })
        except Exception:
            pass

    return {"context": context, "entities": entities, "rules": rules}

# Chargement des ontologies
ontos = load_all_dependencies()
onto_main = get_ontology("file://onto/main_onto.owl").load()
record_pre_reasoning_state(onto_main)

# Génération automatique du contexte NGSI-LD
ngsi_ld_context = generate_ngsi_ld_context(onto_main)

# Extraction des données avec inférences et ajout du contexte
ontology_json = extract_ontology_to_ngsi_ld(onto_main, ngsi_ld_context)

# Sauvegarde
with open("output.json", "w") as f:
    json.dump(ontology_json, f, indent=2)
