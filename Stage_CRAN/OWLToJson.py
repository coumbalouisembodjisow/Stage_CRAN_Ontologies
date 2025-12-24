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

# Enregistre l'état pré-raisonnement des individus
def record_pre_reasoning_state(onto):
    state = {}
    for inst in onto.individuals():
        # Capture les classes directes (hors restrictions)
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
def extract_ontology_to_ngsi_ld(onto):
    sync_reasoner([onto], infer_property_values=True, ignore_unsupported_datatypes=True)

    entities = []
    rules = []
    context = {
        "@context": [
            "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.jsonld",
            "https://schema.lab.fiware.org/ld/context",
            {}
        ]
    }

    # Extraire les entités et mettre à jour le contexte
    for inst in onto.individuals():
        classes = [cls.name for cls in inst.is_a if isinstance(cls, ThingClass)]
        if not classes:
            continue
        main_class = classes[0]
        
        # Ajouter la classe au contexte si elle n'existe pas déjà
        if main_class not in context["@context"][2]:
            cls=onto[main_class]
            for parent_class in cls.is_a:
                if isinstance(parent_class, ThingClass):
                    context["@context"][2][main_class] = parent_class.iri

        # Création de l'entité NGSI-LD
        entity = {
            "id": iri_to_ngsi_ld(inst),
            "type": list(set(cls.name for cls in inst.is_a if isinstance(cls, ThingClass))),
            "name": inst.name
        }

        # Propriétés et relations
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

    # Extraction des règles SWRL
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

    # Retourner les entités, règles et contexte
    return { "context": context,"entities": entities, "rules": rules}

# Chargement des ontologies
ontos = load_all_dependencies()
onto_main = get_ontology("file://onto/AI4C2PS.owl").load()
record_pre_reasoning_state(onto_main)





# 3. Extraction des données avec inférences
ontology_json = extract_ontology_to_ngsi_ld(onto_main)

# Sauvegarde
with open("output_ontology.json", "w") as f:
    json.dump(ontology_json, f, indent=2)