import pydwarf



boneflux_reaction = '''
    [NAME:{name}]
    [BUILDING:KILN:NONE]
    [REAGENT:bone:{bones}:NONE:NONE:NONE:NONE]
        [USE_BODY_COMPONENT]
        [ANY_BONE_MATERIAL]
    [PRODUCT:100:1:BOULDER:NONE:INORGANIC:{product}]
    [FUEL]
    [SKILL:SMELT]
'''

default_product_id = 'CALCITE'

default_reaction_name = 'make calcite from bones'

default_bone_count = 2

default_entities = ['MOUNTAIN', 'PLAINS']

default_file = 'reaction_kiln_boneflux_pineapple'



@pydwarf.urist(
    name = 'pineapple.boneflux',
    version = '1.0.0',
    author = 'Sophie Kirschner',
    description = '''Adds a reaction to the kiln which consumes bones and produces flux.
        Inspired by/stolen from Rubble's Bone Flux mod.''',
    arguments = {
        'product_id': 'ID of the boulder to get out of the reaction. Defaults to CALCITE.',
        'reaction_name': 'The name of the reaction to be shown in the kiln.',
        'bone_count': 'The number of bones required in the reaction.',
        'entities': 'Adds the reaction to these entities. Defaults to MOUNTAIN and PLAINS.',
        'add_to_file': 'Adds the reaction to this file.'
    },
    compatibility = (pydwarf.df_0_2x, pydwarf.df_0_3x, pydwarf.df_0_40)
)
def boneflux(df, product_id=default_product_id, reaction_name=default_reaction_name, bone_count=default_bone_count, entities=default_entities, add_to_file=default_file):
    return pydwarf.urist.getfn('pineapple.utils.addreaction')(
        df,
        id = 'BONE_TO_FLUX_PINEAPPLE',
        tokens = boneflux_reaction % {
            'name': reaction_name,
            'product': product_id,
            'bones': bone_count
        },
        add_to_file = add_to_file,
        permit_entities = entities
    )
