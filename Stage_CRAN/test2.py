from owlready2 import *
from itertools import combinations
world= World ()
onto_ssn = world.get_ontology("onto/ssn.rdf").load()
onto_sosa = world.get_ontology("onto/sosa.rdf").load()
onto_soma = world.get_ontology("http://www.ease-crc.org/ont/SOMA.owl#").load()
onto_core = world.get_ontology("onto/AI4C2PS-core.owl").load()
onto_agent = world.get_ontology("onto/SysAgent.owl").load()
onto_cognition = world.get_ontology("onto/CognitionOnto.owl").load()
onto_dul = world.get_ontology("onto/DUL.owl").load()
onto_main= world.get_ontology("onto/AI4C2PS.owl").load()
onto_humo = world.get_ontology("https://www.ai4c2ps.eu/ontologies/2024/Humo/1.0.0/Humo.owl").load()
with onto_main:
    # Import des ontologies nécessaires
    onto_main.imported_ontologies.append(onto_ssn)
    onto_main.imported_ontologies.append(onto_sosa)
    onto_main.imported_ontologies.append(onto_soma)
    onto_main.imported_ontologies.append(onto_core)
    onto_main.imported_ontologies.append(onto_agent)
    onto_main.imported_ontologies.append(onto_cognition)
    onto_main.imported_ontologies.append(onto_dul)

ontologies= [
    onto_ssn,
    onto_sosa,
    onto_soma,
    onto_core,
    onto_agent,
    onto_cognition,
    onto_dul,
    onto_humo,
    onto_main
]

    
    
for cls in onto_main.indirectly_imported_ontologies():
    print("Class:", cls.name)
