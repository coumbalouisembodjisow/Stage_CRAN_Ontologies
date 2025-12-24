import json
from owlready2 import *

world = World()
# Charge chaque ontologie locale séparément
onto_ssn = world.get_ontology("onto/ssn.rdf").load()
onto_sosa = world.get_ontology("onto/sosa.rdf").load()
onto_soma=world.get_ontology("http://www.ease-crc.org/ont/SOMA.owl#").load()
onto_core = world.get_ontology("onto/AI4C2PS-core.owl").load()
onto_agent= world.get_ontology("onto/SysAgent.owl").load()
onto_cognition = world.get_ontology("onto/CognitionOnto.owl").load()
onto_dul= world.get_ontology("http://www.ontologydesignpatterns.org/ont/dul/DUL.owl").load()
onto_main =world.get_ontology("onto/AI4C2PS.owl").load() # This ontology  imports the others

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

    #  HelicalMotion ≡ Movement ⊓ ∃hasRotation.Rotation ⊓ ∃hasTranslation.Translation
    HelicalMotion.equivalent_to.append(
        onto_soma.Motion 
        & Restriction(hasRotation, SOME, Rotation) 
        & Restriction(hasTranslation, SOME, Translation)
    )
    class isMotionFor(ObjectProperty):
        domain = [HelicalMotion]
        range = [onto_dul.Task]
        comment = [
            "Links the helical motion to the task that requires it (e.g., ScrewingTask)."
        ]
        
    class hasPitch(DataProperty):
        domain = [HelicalMotion]
        range = [float]
        comment = [
            "The thread pitch of the motion, expressed in millimeters (e.g., 1.5)."
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
# Fusionne les ontologies en important les autres dans la principale
with onto_main:
    onto_main.imported_ontologies.append(onto_ssn)
    onto_main.imported_ontologies.append(onto_sosa)
    onto_main.imported_ontologies.append(onto_soma)
    onto_main.imported_ontologies.append(onto_agent)
    onto_main.imported_ontologies.append(onto_cognition)
    onto_main.imported_ontologies.append(onto_dul)
    onto_main.imported_ontologies.append(onto_core)
    #onto_main.imported_ontologies.append(onto_humo)
# Fonction pour copier les classes

def merge_classes(source_onto, target_onto):
    with target_onto:
        for cls in source_onto.classes():
            types.new_class(cls.name, (cls,))

def extract_classes(expr):
    """Récupère les classes simples d'une expression (Or, And, etc.)"""
    if isinstance(expr, ThingClass):
        return [expr]
    elif hasattr(expr, 'Classes'):
        return list(expr.Classes)
    else:
        return []

            
def merge_properties(source_onto, target_onto):
    target_classes = {cls.name: cls for cls in target_onto.classes()}

    with target_onto:
        for prop in source_onto.object_properties():
            new_prop = types.new_class(prop.name, (ObjectProperty,))            
            # Copier le domaine
            new_domains = []
            for d in prop.domain:
                for cls in extract_classes(d):
                    if cls.name in target_classes:
                        new_domains.append(target_classes[cls.name])
            if new_domains:
                new_prop.domain = new_domains

            # Copier le range
            new_ranges = []
            for r in prop.range:
                for cls in extract_classes(r):
                    if cls.name in target_classes:
                        new_ranges.append(target_classes[cls.name])
            if new_ranges:
                new_prop.range = new_ranges

        for prop in source_onto.data_properties():
            new_prop = types.new_class(prop.name, (DataProperty,))
            
            new_domains = []
            for d in prop.domain:
                for cls in extract_classes(d):
                    if cls.name in target_classes:
                        new_domains.append(target_classes[cls.name])
            if new_domains:
                new_prop.domain = new_domains
            
            if prop.range:
                new_prop.range = list(prop.range)

# Copie les classes de toutes les ontologies dans la principale
merge_classes(onto_core, onto_main)
merge_classes(onto_ssn, onto_main)
merge_classes(onto_sosa, onto_main)
merge_classes(onto_agent, onto_main)
merge_classes(onto_cognition, onto_main)
merge_classes(onto_soma, onto_main)
merge_classes(onto_dul, onto_main)
# Copie les propriétés de toutes les ontologies dans la principale
merge_properties(onto_core, onto_main)
merge_properties(onto_ssn, onto_main)
merge_properties(onto_sosa, onto_main)
merge_properties(onto_agent, onto_main)
merge_properties(onto_cognition, onto_main)
merge_properties(onto_soma, onto_main)
merge_properties(onto_dul, onto_main)
#merge_properties(onto_humo, onto_main)

def find_class(class_name):
        return getattr(onto_main, class_name, None)


# Fonction pour créer les instances à partir des données NGSI-LD
def create_instances_ngsi_ld(graph_data, onto_main):
    instances = {}    
    for obj in graph_data:
        obj_id = obj.get("id")
        obj_type = obj.get("type")
        obj_name = obj_id.split(":")[-1] 
        if not obj_id or not obj_type:
            continue
        if isinstance(obj_type, list):
            primary_type = obj_type[0]
            other_types = obj_type[1:]
        else:
            primary_type = obj_type
            other_types = []
        # Find the class in the ontology
        class_obj = find_class(primary_type)
        if class_obj:
            inst = class_obj(obj_name) # create instance with the name
            instances[obj_name] = inst

            # Ajouter les types supplémentaires (subclasses)
            for ot in other_types:
                other_class = find_class(ot.split(":")[-1])
                if other_class:
                    inst.is_a.append(other_class)

    return instances

def add_properties_ngsi_ld(graph_data, instances, onto_main):
    
    for obj in graph_data:
        obj_id = obj.get("id").split(":")[-1]  # Dernière partie de l'ID comme nom
        inst = instances.get(obj_id)
        if not inst:
            continue

        # Parcours de chaque propriété de l'objet (à l'exception de id et type)
        for prop, val in obj.items():
            if prop in ("id", "type","name"):
                continue

            # Recherche la propriété dans l'ontologie
            prop_obj = world.search_one(iri="*" + prop)
            if prop_obj is None:
                continue

            try:
                # Propriété objet (relation avec d'autres instances)
                if isinstance(prop_obj, ObjectPropertyClass):
                    # Normaliser les valeurs en liste
                    values = val if isinstance(val, list) else [val]
                    for v in values:
                        target_id = None
                        if isinstance(v, dict) and "object" in v:
                            target_id = v["object"].split(":")[-1]  # Dernière partie de Object comme nom de l'instance
                           
                        # Cas 2: Valeur est une chaîne (IRI directe)
                        elif isinstance(v, str):
                            target_id = v
                        
                        if not target_id:
                            continue
                            
                        target = instances.get(target_id)
                       
                        if target:
                            # Ajouter la relation (si l'objet de destination existe)
                            getattr(inst, prop).append(target)
                
                # Propriété de données (valeurs simples, comme des chaînes ou des nombres)
                elif isinstance(prop_obj, DataPropertyClass):
                    
                    values = val if isinstance(val, list) else [val]
                    for v in values:
                        if isinstance(v, dict) and "value" in v: 
                            v = v["value"]

                        prop_obj[inst].append(v)


            except Exception as e:
                print(f" Erreur avec '{prop}' sur '{inst}': {e}")


with open("screwing.json", "r") as f: # load the NGSI-LD data
    data = json.load(f)
    graph_data = data.get("@graph", data)  
with onto_main:
    #create instances from the NGSI-LD data
    instances = create_instances_ngsi_ld(graph_data, onto_main)
    # add properties to the instances
    add_properties_ngsi_ld(graph_data, instances, onto_main)

with onto_main:
    # Rule to infer that an agent has an ability based on
    # the tool it has and the capability described by an affordance
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
onto_main.save(file="onto/AI4C2PS.owl")
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

onto_main.save(file="onto/AI4C2PS.owl")

cobot= onto_main.ur5
print(cobot.is_a)
action= onto_main.screwBoltAction_1
print(action.performedBy)