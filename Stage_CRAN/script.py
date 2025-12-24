from owlready2 import *
import json
import re

# 1. Configuration Initiale
world = World()
# Charger les ontologies spécifiques
onto_ssn = world.get_ontology("onto/ssn.rdf").load()
onto_sosa = world.get_ontology("onto/sosa.rdf").load()
onto_soma = world.get_ontology("onto/SOMA.owl").load()
onto_core = world.get_ontology("onto/AI4C2PS-core.owl").load()
onto_agent = world.get_ontology("onto/SysAgent.owl").load()
onto_cognition = world.get_ontology("onto/CognitionOnto.owl").load()
onto_dul = world.get_ontology("onto/DUL.owl").load()


onto_ssn.hasInput.domain=[onto_dul.Action]
onto_ssn.hasInput.range=[onto_dul.Object]
onto_ssn.hasOutput.domain=[onto_dul.Action]
onto_ssn.hasOutput.range=[onto_dul.Object]
onto_ssn.save(file="onto/ssn.rdf")

with onto_soma:
    class hasGoalLocalization(ObjectProperty):
        domain = [onto_soma.Positioning]
        range = [onto_soma.Localization]
        comment = ["Relates a Positioning task to the target Localization where the object should be placed."]
    class Screwability(onto_soma.Disposition):
        equivalent_to = [
            onto_soma.Disposition
            & (onto_dul.isDescribedBy.exactly(1,
                onto_soma.Affordance
                & (onto_soma.definesBearer.exactly(1, onto_dul.Role))
                & (onto_soma.definesTrigger.exactly(1, onto_dul.Role))
                & (onto_dul.definesTask.exactly(1, onto_dul.Task))
            ))
        ]
        comment = [
            "Capability representing the potential to perform a screwing task, "
            "characterized by its associated affordance, trigger, bearer, and task."
        ]
    class Rotation(onto_soma.Motion): pass
    class Translation(onto_soma.Motion): pass
    class HelicalMotion(onto_soma.Motion): pass

    # Définir les propriétés d’objet
    hasRotation = ObjectProperty()
    hasRotation.domain = [onto_soma.Motion]
    hasRotation.range = [Rotation]

    hasTranslation = ObjectProperty()
    hasTranslation.domain = [onto_soma.Motion]
    hasTranslation.range = [Translation]

    # Définir les propriétés de données (optionnel)
    hasAngle = DataProperty()
    hasAngle.domain = [Rotation]
    hasAngle.range = [float]

    hasDistance = DataProperty()
    hasDistance.domain = [Translation]
    hasDistance.range = [float]

    # Définir l'équivalence logique : HelicalMotion ≡ Movement ⊓ ∃hasRotation.Rotation ⊓ ∃hasTranslation.Translation
    HelicalMotion.equivalent_to.append(
        onto_soma.Motion 
        & Restriction(hasRotation, SOME, Rotation) 
        & Restriction(hasTranslation, SOME, Translation)
    )

    class hasPitch(DataProperty):
        domain = [HelicalMotion]
        range = [float]
        comment = [
            "The thread pitch of the motion, expressed in millimeters (e.g., 1.5)."
        ]

    
    class isMotionFor(ObjectProperty):
        domain = [HelicalMotion]
        range = [onto_dul.Task]
        comment = [
            "Links the helical motion to the task that requires it (e.g., ScrewingTask)."
        ]

onto_soma.save("onto/SOMA.owl")

with onto_dul:
    class performedBy(ObjectProperty):
        domain=[onto_dul.Action]
        range=[onto_dul.Agent]
        comment=["Represents the relationship between an action and the agent (e.g., robot or human) performing that action."]
        
    class canPerform(ObjectProperty):
        domain = [onto_dul.Agent]
        range = [onto_dul.Action]
        comment = ["Indicates that an agent has the ability or authorization to perform a given action."]

    class isFirstSubtask(DataProperty,FunctionalProperty):
        domain = [onto_dul.Task]  # apply to tasks
        range = [bool]  
        comment = ["Mark the first subtask of a parent task"]

    class isLastSubtask(DataProperty,FunctionalProperty):
        domain = [onto_dul.Task]  #apply to tasks
        range = [bool]   
        comment = ["Mark the last subtask of a parent task"]
    class hasStepNumber(DataProperty):
        domain = [onto_dul.Task]
        range = [str]
        comment = ["Indicates the step number in a sequence of tasks."]
    class hasActionNumber(DataProperty):
        domain=[onto_dul.Action]
        range=[str]
onto_dul.save("onto/DUL.owl")


ONTOLOGY_FILES = {
    "http://www.w3.org/ns/sosa#": "onto/sosa.rdf",
    "http://www.w3.org/ns/ssn#": "onto/ssn.rdf",
    "http://www.ease-crc.org/ont/SOMA.owl#": "onto/SOMA.owl",
    "https://www.ai4c2ps.eu/ontologies/2024/core#": "onto/AI4C2PS-core.owl",
    "https://www.ai4c2ps.eu/ontologies/2024/SysAgentOnto#": "onto/SysAgent.owl",
    "https://www.ai4c2ps.eu/ontologies/2024/CognitionOntology#": "onto/CognitionOnto.owl",
    "http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#": "onto/DUL.owl"
}

def setup_world():
    """Initialise le monde OWL et charge les ontologies"""
    
    return world, {
        "http://www.w3.org/ns/sosa#": onto_sosa,
        "http://www.w3.org/ns/ssn#": onto_ssn,
        "http://www.ease-crc.org/ont/SOMA.owl#": onto_soma,
        "https://www.ai4c2ps.eu/ontologies/2024/core#": onto_core,
        "https://www.ai4c2ps.eu/ontologies/2024/SysAgentOnto#": onto_agent,
        "https://www.ai4c2ps.eu/ontologies/2024/CognitionOntology#": onto_cognition,
        "http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#": onto_dul
    }

world, ontologies = setup_world()
    
# 2. Trouver l'ontologie cible à partir du contexte
def find_target_ontology(class_iri, ontologies):
    """Détermine l'ontologie cible basée sur l'IRI complet de la classe"""
    # Extraire l'IRI de base
    base_iri = re.match(r"(^[^#]+#)", class_iri).group(1)
    
    # Trouver l'ontologie correspondante
    for base, onto in ontologies.items():
        if base_iri.startswith(base):
            return onto
    
    raise ValueError(f"Aucune ontologie trouvée pour l'IRI {class_iri}")
def find_iri_in_context(context_list, term):
    """Trouve l'IRI correspondant à un terme dans la liste de contexte"""
    # Parcourir tous les éléments du contexte
    for item in context_list:
        # Si l'élément est un dictionnaire et contient le terme
        if isinstance(item, dict) and term in item:
            return item[term]
    
def get_source_ontology(inst, ontologies):
    """Trouve l'ontologie source d'une instance"""
    for base_iri, onto in ontologies.items():
        # Compare les IRIs de base
        if inst.iri.startswith(base_iri):
            return onto
    return None  # ou une ontologie par défaut si nécessaire
# 3. Fonction d'instanciation principale
def create_instances(graph_data, ontologies, context):
    """Crée les instances dans les ontologies appropriées en utilisant le contexte"""
    instances = {}
    
    for entity in graph_data:
        entity_id = entity["id"]
        entity_types = entity["type"] if isinstance(entity["type"], list) else [entity["type"]]
        
        # Trouver l'IRI complet de la classe principale via le contexte
        main_type = entity_types[0]
        class_iri = find_iri_in_context(context, main_type)
        
        # Trouver l'ontologie cible
        onto_target = find_target_ontology(class_iri, ontologies)
        
        with onto_target:
            # Créer l'instance
            instance_name = entity_id.split(":")[-1]
            
            # Vérifier si la classe existe
            cls = None
            try:
                cls = world[class_iri]
                
            
            except:
                # Créer la classe si elle n'existe pas
                cls = types.new_class(main_type, (Thing,))
                cls.iri = class_iri
    
            inst = cls(instance_name)
            instances[entity_id] = inst
            
            # Ajouter les types supplémentaires
            for additional_type in entity_types[1:]:
                additional_iri = find_iri_in_context(context, additional_type)
                
                # Créer la classe si nécessaire
                if not world[additional_iri]:
                    with onto_target:
                        additional_cls = types.new_class(additional_type, (Thing,))
                        additional_cls.iri = additional_iri
                
                inst.is_a.append(world[additional_iri])
    
    return instances

# 4. Fonction d'ajout des propriétés
def add_properties(graph_data, instances, ontologies_dict, context):
    """Ajoute les propriétés directement dans les fichiers locaux"""
    # Vérifier que les ontologies sont chargées
    if not ontologies_dict:
       
        return
    
    # Traiter chaque entité
    for entity in graph_data:
        entity_id = entity["id"]
        
        # Extraire l'identifiant simple (dernière partie après '#' ou '/')
        simple_id = entity_id.split("#")[-1] if "#" in entity_id else entity_id.split("/")[-1]
        inst = instances.get(simple_id)
        
        if not inst:
            continue
        
        # Trouver l'ontologie source et son fichier
        source_ontology = None
        file_path = None
        
        # 1. Essayer de trouver par IRI complet
        for base_iri, onto in ontologies_dict.items():
            if inst.iri.startswith(base_iri):
                source_ontology = onto
                file_path = ONTOLOGY_FILES.get(base_iri)
                break
        
        # 2. Si non trouvé, essayer de trouver par fragment
        
        if not source_ontology:
            for base_iri, onto in ontologies_dict.items():
                if "#" + simple_id in inst.iri:
                    source_ontology = onto
                    file_path = ONTOLOGY_FILES.get(base_iri)
                    break
        
        if not source_ontology or not file_path:
            
            continue
        
        # Travailler dans le contexte de l'ontologie
        with source_ontology:
            # Trouver l'instance dans l'ontologie locale
            local_inst = source_ontology.search(iri=inst.iri)
            if not local_inst:
               
                continue
            
            local_inst = local_inst[0]
            
            # Traiter chaque propriété
            for prop_name, prop_value in entity.items():
                if prop_name in ["id", "type", "@context", "name"]:
                    continue
                
                # Recherche la propriété dans l'ontologie
                prop_obj = world.search_one(iri="*" + prop_name)
                if prop_obj is None:
                   
                    continue
                
                try:
                    # Normaliser les valeurs
                    values = prop_value if isinstance(prop_value, list) else [prop_value]
                    
                    # Propriété d'objet (relation)
                    if isinstance(prop_obj, ObjectPropertyClass):
                        for v in values:
                            target_id = None
                            
                            # Extraire l'ID de la cible
                            if isinstance(v, dict) and "object" in v:
                                target_id = v["object"]
                            elif isinstance(v, str):
                                target_id = v
                            
                            if not target_id:
                                continue
                            
                            # Simplifier l'ID de la cible
                            target_simple_id = target_id.split("#")[-1] if "#" in target_id else target_id.split("/")[-1]
                            
                            # Trouver l'instance cible
                            target = instances.get(target_simple_id)
                            if target:
                                # Ajouter la relation
                                getattr(local_inst, prop_name).append(target)
                                
                    
                    # Propriété de données
                    elif isinstance(prop_obj, DataPropertyClass):
                        for v in values:
                            # Extraire la valeur
                            if isinstance(v, dict) and "value" in v:
                                v = v["value"]
                            
                            # Ajouter la valeur
                            getattr(local_inst, prop_name).append(v)
                           
                
                except Exception as e:
                    print(f"🔥 Erreur avec '{prop_name}' sur '{entity_id}': {e}")
        
        # Sauvegarder dans le fichier local
        source_ontology.save(file=file_path)
        

# Charger les données NGSI-LD avec contexte
with open("screwing.json", "r") as f:
        ngsi_data = json.load(f)
        graph_data = ngsi_data.get("@graph", ngsi_data)
        context = ngsi_data.get("@context", ngsi_data)
    # Création des instances
        instances = create_instances(graph_data, ontologies, context)
    
    # Ajout des propriétés
        add_properties(graph_data, instances,ontologies,context)
    
def create_modular_ontology(input_ontos, output_path):
    """Crée une ontologie modulaire avec conservation de la provenance"""
    # Créer une nouvelle ontologie principale
    main_onto = get_ontology("http://www.ai4c2ps.eu/ontologies/2024/")
    
    # Dictionnaire pour suivre les mappings
    class_mappings = {}
    prop_mappings = {}
    
    # Charger et importer chaque ontologie
    for prefix, path in input_ontos.items():
        
        onto = get_ontology(path).load()
        
        # Ajouter l'import
        main_onto.imported_ontologies.append(onto)
        with main_onto:
            for cls in onto.classes():
                # Créer un alias dans l'ontologie principale
                
                    # Créer une nouvelle classe qui hérite de la classe originale
                    #new_cls = types.new_class(cls.name, (cls,))
                    #class_mappings[cls.iri] = new_cls
                    types.new_class(cls.name, (cls,))
                    
        
        # Mapper les propriétés
        for prop in onto.properties():
            # Créer un alias dans l'ontologie principale
            with main_onto:
                if isinstance(prop, ObjectPropertyClass):
                    new_prop = types.new_class(prop.name, (prop, ObjectProperty,))
                elif isinstance(prop, DataPropertyClass):
                    new_prop = types.new_class(prop.name, (prop, DataProperty,))
                else:
                    new_prop = types.new_class(prop.name, (prop, AnnotationProperty,))
                
                prop_mappings[prop.iri] = new_prop
    
   
    main_onto.save(file=output_path)
    return main_onto, class_mappings, prop_mappings
create_modular_ontology(ONTOLOGY_FILES, "onto/main.owl")

def create_instances_ngsi_ld(graph_data,onto_main ,context):
    """Crée les instances dans les ontologies appropriées en utilisant le contexte"""
    instances = {}
    
    for entity in graph_data:
        entity_id = entity["id"]
        entity_types = entity["type"] if isinstance(entity["type"], list) else [entity["type"]]
        
        # Trouver l'IRI complet de la classe principale via le contexte
        main_type = entity_types[0]
        class_iri = find_iri_in_context(context, main_type)
        
        
        
        with onto_main:
            # Créer l'instance
            instance_name = entity_id.split(":")[-1]
            
            # Vérifier si la classe existe
            cls = None
            try:
                cls = onto_main.search_one(iri=class_iri)
            except:
                # Créer la classe si elle n'existe pas
                cls = types.new_class(main_type, (Thing,))
                
                cls.iri = class_iri
            
            inst = cls(instance_name)
            
            instances[entity_id] = inst
            
            # Ajouter les types supplémentaires
            for additional_type in entity_types[1:]:
                additional_iri = find_iri_in_context(context, additional_type)
                
                # Créer la classe si nécessaire
                if not  onto_main.search_one(iri=class_iri):
                    with onto_main:
                        additional_cls = types.new_class(additional_type, (Thing,))
                        additional_cls.iri = additional_iri
                
                inst.is_a.append(world[additional_iri])
    
    # Sauvegarder l'ontologie principale
    onto_main.save(file="onto/main.owl")
    return instances

def add_properties_ngsi_ld(graph_data, instances, onto_main,context):
    
    # Traiter chaque entité
    for entity in graph_data:
        entity_id = entity["id"]
        
        # Extraire l'identifiant simple (dernière partie après '#' ou '/')
        simple_id = entity_id.split("#")[-1] if "#" in entity_id else entity_id.split("/")[-1]
        inst = instances.get(simple_id)
        
        
            
            # Traiter chaque propriété
        for prop_name, prop_value in entity.items():
                if prop_name in ["id", "type", "@context", "name"]:
                    continue
                
                # Recherche la propriété dans l'ontologie
                prop_obj = world.search_one(iri="*" + prop_name)
                if prop_obj is None:
                   
                    continue
                
                try:
                    # Normaliser les valeurs
                    values = prop_value if isinstance(prop_value, list) else [prop_value]
                    
                    # Propriété d'objet (relation)
                    if isinstance(prop_obj, ObjectPropertyClass):
                        for v in values:
                            target_id = None
                            
                            # Extraire l'ID de la cible
                            if isinstance(v, dict) and "object" in v:
                                target_id = v["object"]
                            elif isinstance(v, str):
                                target_id = v
                            
                            if not target_id:
                                continue
                            
                            # Simplifier l'ID de la cible
                            target_simple_id = target_id.split("#")[-1] if "#" in target_id else target_id.split("/")[-1]
                            
                            # Trouver l'instance cible
                            target = instances.get(target_simple_id)
                            if target:
                                # Ajouter la relation
                                getattr(inst, prop_name).append(target)
                                
                    
                    # Propriété de données
                    elif isinstance(prop_obj, DataPropertyClass):
                        for v in values:
                            # Extraire la valeur
                            if isinstance(v, dict) and "value" in v:
                                v = v["value"]
                            
                            # Ajouter la valeur
                            getattr(inst, prop_name).append(v)
                           
                
                except Exception as e:
                    print(f"🔥 Erreur avec '{prop_name}' sur '{entity_id}': {e}")
        
        # Sauvegarder dans le fichier local
        onto_main.save(file="onto/main.owl")
        

onto_main = get_ontology("onto/main.owl").load()
with onto_main:
    instances=create_instances_ngsi_ld(graph_data, onto_main, context)
    add_properties_ngsi_ld(graph_data, instances, onto_main,context)

with onto_main:
    # Règle qui permet d'inférer qu'un agent a une ability
    rule = Imp(name = "HasAbilityRule")  # nom interne pour la retrouver
    rule.set_as_rule("""            
        Capability(?ab) ^  Agent (?ag ) ^hasPart(?ag, ?tool) ^
        hasDisposition(?tool, ?ab) ^ 
        isDescribedBy(?ab, ?aff) ^ 
        definesBearer(?aff, ?bear) ^ hasRole(?obj, ?bear) ^ 
        definesTrigger(?aff, ?trig) ^ hasRole(?tool, ?trig) 
        -> hasAbility(?ag, ?ab)
    """)
    
    # Règle qui permet d'inférer qu'une action suit une autre action
    # en fonction de la relation "follows" entre les tâches associées
    # et de l'exécution des tâches dans des actions spécifiques
    # Cette règle est utile pour établir des dépendances entre les actions
    # en fonction de l'ordre d'exécution des tâches
    rule = Imp(name="FollowsActionRule")
    rule.set_as_rule("""
    Task(?t1) ^ Task(?t2) 
    ^ follows(?t2, ?t1)
    ^ isExecutedIn(?t1, ?a1)
    ^ isExecutedIn(?t2, ?a2) 
    -> follows(?a2, ?a1)
""")
    # Règle qui permet d'inférer que si une tâche B suit une tâche A , la première sous-tâche de B suit la dernière sous-tâche de A
    # Cette règle est utile pour établir des relations de dépendance entre les sous-tâches
    # en fonction de l'ordre d'exécution des tâches
    # et de la structure des sous-tâches
    rule = Imp(name="FollowsPartRule")
    rule.set_as_rule("""
                     
    Task(?A) ^ Task(?B) ^ directlyFollows(?B,?A) ^ hasPart(?A, ?lastA)
    ^ isLastSubtask(?lastA, true) ^ hasPart(?B, ?firstB) ^ isFirstSubtask(?firstB, true)
    -> directlyFollows(?firstB, ?lastA)
    
    """)
    
    # Post-traitement pour renommer les Ability déduites
    def rename_abilities():
        # Trouver toutes les relations hasAbility créées par la règle
        for agent, ability in onto_main.hasAbility.get_relations():
            if isinstance(ability, onto_main.Capability):
                # Générer un nouveau nom basé sur la Capability
                cap_name = ability.name
                new_name = f"can{cap_name.capitalize().replace('ability', '')}"
                
                # Créer une nouvelle Ability avec le nom transformé
                new_ability = onto_main.Ability(new_name)
                
                # Transférer les relations
                new_ability.is_a = ability.is_a
                for prop in onto_main.object_properties():
                    for value in prop[ability]:
                        prop[new_ability].append(value)
                
                # Mettre à jour la relation
                onto_main.hasAbility[agent].remove(ability)
                onto_main.hasAbility[agent].append(new_ability)
                
                # Supprimer l'ancienne Capability
                destroy_entity(ability)
sync_reasoner([onto_main], infer_property_values=True,ignore_unsupported_datatypes = True)
rename_abilities()

canScrew = onto_main.canScrew

for task in onto_main.Screwing.instances():
            if not task.requiresAbility:
                task.requiresAbility.append(canScrew)
onto_main.save(file="onto/main.owl")
# Vérification unicité des hasStepNumber
step_numbers = set()
for task in onto_main.Task.instances():
    for num in task.hasStepNumber:
        if num in step_numbers:
            print(f"[Erreur] Numéro de step non unique : {num}")
        else:
            step_numbers.add(num)

# Vérification unicité des hasActionNumber
action_numbers = set()
for action in onto_main.Action.instances():
    for num in action.hasActionNumber:
        if num in action_numbers:
            print(f"[Erreur] Numéro d'action non unique : {num}")
        else:
            action_numbers.add(num)
with onto_main:
    # Règle qui permet de vérifier si le Cobot a les abilities requises pour exécuter une action
    rule = Imp(name="CanPerformRule")
    rule.set_as_rule("""
                     
         Task(?t) ^ requiresAbility(?t, ?ab) ^isExecutedIn(?t, ?a) 
         ^Cobot(?co) ^hasAbility(?co, ?ab)
        -> canPerform(?co, ?a)
        
    """)
    
    
    # Règle qui permet d'assigner ,au cobot , une action censée être faite par l'opérateur si ce dernier ne l'exécute  pas 
    rule = Imp(name="FallbackToCobot")
    rule.set_as_rule("""
        Action(?a) ^Operator(?op) ^performedBy(?a, ?op) ^
        hasExecutionState(?a, executionStatePending) ^ Cobot(?co) ^
        canPerform(?co, ?a) -> performedBy(?a, ?co)
    """)
    
    def order_subtasks():
        for task in onto_main.Task.instances():
            subtasks = list(task.hasPart)
            
            if subtasks:
                # Trier en convertissant les numéros en tuples numériques
                try:
                    subtasks.sort(key=lambda t: tuple(
                        map(int, t.hasStepNumber[0].split('.')) 
                        if t.hasStepNumber else (0,)
                    ))
                except:
                    # Fallback pour les formats non standard
                    subtasks.sort(key=lambda t: t.hasStepNumber[0] if t.hasStepNumber else "")
                
                # Réinitialiser les marqueurs
                for subtask in subtasks:
                    subtask.isFirstSubtask =[]
                    subtask.isLastSubtask = []
                
                # Marquer la première
                subtasks[0].isFirstSubtask =[ True]
                
                # Marquer la dernière
                subtasks[-1].isLastSubtask = [True]
order_subtasks()
sync_reasoner([onto_main], infer_property_values=True,ignore_unsupported_datatypes = True)
onto_main.save(file="onto/main.owl")
cobot=onto_main.ur5
print(cobot.is_a)