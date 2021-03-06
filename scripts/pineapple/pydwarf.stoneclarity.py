# vim:fileencoding=UTF-8

import pydwarf
import raws

# Generic mutators for use in rules
def mutator_generic(value, *args):
    def fn(inorganic):
        tokenresult = inorganic.stoneclarity[value]
        if tokenresult and len(tokenresult):
            token = tokenresult[0]
            for i in xrange(min(len(args), len(token.args))):
                if args[i] is not None: token.args[i] = args[i]
    return fn
def mutator_remove(value):
    def fn(inorganic):
        tokenresult = inorganic.stoneclarity[value]
        if tokenresult:
            for result in tokenresult: result.remove()
    return fn
# Generic filters
def filter_ore_veins(value):
    return len(value.stoneclarity['ORE']) and any([env.args[1] == 'VEIN' for env in (value.stoneclarity['ENVIRONMENT'] + value.stoneclarity['ENVIRONMENT_SPEC'])])

# Default to these rules when none are passed
default_rules = [
    # Make all flux stone have a white foreground
    {
        # Gives the rule a name, makes logs pretty
        'name': 'flux',
        # Indicates that this rule applies to inorganics in the FLUX group: That is, ones which have a
        # [REACTION_CLASS:FLUX] token in their properties.
        'group': 'FLUX',
        # Each given mutator function is run for each matching inorganic, with that token as the argument.
        # Tokens will have a stoneclarity attribute which contains the results of the query which targeted it.
        # Here, mutator_generic returns a closure in order to keep things convenient.
        'mutator': mutator_generic('DISPLAY_COLOR', 7, None, 1)
    },
    # Make all fuel be represented by * on the map and in stockpiles
    {
        'name': 'fuel',
        'group': 'FUEL',
        'mutator': (mutator_generic('TILE', "'*'"), mutator_generic('ITEM_SYMBOL', "'*'"))
    },
    # Make cobaltite not look like ore
    {
        'name': 'cobaltite',
        'id': 'COBALTITE', # Applies only to cobaltite
        'mutator': (mutator_generic('TILE', "'%'"), mutator_remove('ITEM_SYMBOL'))
    },
    # Make all ores in veins be represented by £ on the map and * in stockpiles
    {
        'name': 'ore',
        'filter': filter_ore_veins, # Applies to anything matching the filter: That is, an ore which appears in veins.
        'mutator': (mutator_generic('TILE', '156'), mutator_generic('ITEM_SYMBOL', "'*'"))
    },
    # Make all gems be represented by ☼ on the map and in stockpiles
    {
        'name': 'gem',
        'group': 'GEM',
        'mutator': (mutator_generic('TILE', '15'), mutator_generic('ITEM_SYMBOL', '15'))
    }
]

# You should specify fuels=vanilla_fuels if you know that no prior mod has modified DF's fuels
vanilla_fuels = ['COAL_BITUMINOUS', 'LIGNITE']

# Pass this dict when querying, starting with some INORGANIC, to find relevant tokens all in one go
# ENVIRONMENT, ENVIRONMENT_SPEC, and FUEL groups are handled specially. Everything else is simply
# a boolean check for a match, and matches get placed in the group identified by the key to which
# a token query is matched.
def propertyfilter(**kwargs): return raws.tokenfilter(limit=1, limit_terminates=False, **kwargs) # Convenience function
default_inorganics_query = {
    # Detect tokens which indicate what kind of inorganic this is
    'STONE': propertyfilter(exact_value='IS_STONE'),
    'GEM': propertyfilter(exact_value='IS_GEM'),
    'ORE': propertyfilter(exact_value='METAL_ORE'),
    'FLUX': propertyfilter(pretty='REACTION_CLASS:FLUX'),
    'GYPSUM': propertyfilter(pretty='REACTION_CLASS:GYPSUM'),
    'SOIL': propertyfilter(exact_value='SOIL'),
    'SOIL_SAND': propertyfilter(exact_value='SOIL_SAND'),
    'SOIL_OCEAN': propertyfilter(exact_value='SOIL_OCEAN'),
    'METAMORPHIC': propertyfilter(exact_value='METAMORPHIC'),
    'SEDIMENTARY': propertyfilter(exact_value='SEDIMENTARY'),
    'IGNEOUS_ALL': propertyfilter(exact_value='IGNEOUS_ALL'),
    'IGNEOUS_EXTRUSIVE': propertyfilter(exact_value='IGNEOUS_EXTRUSIVE'),
    'IGNEOUS_INTRUSIVE': propertyfilter(exact_value='IGNEOUS_INTRUSIVE'),
    'AQUIFER': propertyfilter(exact_value='AQUIFER'),
    'NO_STONE_STOCKPILE': propertyfilter(exact_value='NO_STONE_STOCKPILE'),
    'ENVIRONMENT': raws.tokenfilter(exact_value='ENVIRONMENT'),
    'ENVIRONMENT_SPEC': raws.tokenfilter(exact_value='ENVIRONMENT_SPEC'),
    # Detect tokens which represent appearance
    'TILE': propertyfilter(exact_value='TILE'),
    'ITEM_SYMBOL': propertyfilter(exact_value='ITEM_SYMBOL'),
    'DISPLAY_COLOR': propertyfilter(exact_value='DISPLAY_COLOR'),
    'BASIC_COLOR': propertyfilter(exact_value='BASIC_COLOR'),
    'TILE_COLOR': propertyfilter(exact_value='TILE_COLOR'),
    'STATE_COLOR': raws.tokenfilter(exact_value='STATE_COLOR'),
    # Stop at the next [INORGANIC:] token
    'EOF': raws.tokenfilter(exact_value='INORGANIC', limit=1)
}

# Automatically get a list of INORGANIC IDs which describe fuels
def autofuels(dfraws, log=None):
    if log: log.info('No fuels specified, detecting...')
    fuels = []
    for reaction in dfraws.all(exact_value='REACTION'): # For each reaction:
        # Does this reaction produce coke?
        reactionmakescoke = False
        for product in reaction.alluntil(exact_value='PRODUCT', until_exact_value='REACTION'):
            if product.args[-1] == 'COKE':
                if log: log.debug('Found coke-producing reaction %s with product %s.' % (reaction, product))
                reactionmakescoke = True
                break
        if reactionmakescoke:
            for reagent in reaction.alluntil(exact_value='REAGENT', until_exact_value='REACTION'):
                if log: pydwarf.log.debug('Identified reagent %s as referring to a fuel.' % (reagent))
                fuels.append(reagent.args[-1])
    if log: log.info('Finished detecting fuels! These are the ones I found: %s' % fuels)
    if not len(fuels): log.warning('Oops, failed to find any fuels.')
    return fuels

# Build dictionaries which inform stoneclarity of how various inorganics might be identified
def builddicts(query, dfraws, fuels, log=None):
    if log: log.debug('Building dicts...')
    groups = {}
    ids = {}
    inorganics = dfraws.all(exact_value='INORGANIC')
    if log: log.info('I found %d inorganics. Processing...' % len(inorganics))
    for token in inorganics:
        # Get results of query
        query = token.query(query)
        token.stoneclarity = {i: j.result for i, j in query.iteritems()}
        # Handle the simpler groups, 1:1 correspondence between whether some property was found and whether the inorganic belongs in some group
        for groupname in token.stoneclarity:
            if len(token.stoneclarity[groupname]):
                if groupname not in groups: groups[groupname] = set()
                groups[groupname].add(token)
        # Handle metamorphic, sedimentary, igneous
        # Also veins and clusters, etc.
        for env in token.stoneclarity['ENVIRONMENT']:
            if env.nargs() >= 2:
                envtype = 'ENVIRONMENT_'+env.args[0]
                veintype = 'ENVIRONMENT_'+env.args[1]
                if envtype not in groups: groups[envtype] = set()
                if veintype not in groups: groups[veintype] = set()
                groups[envtype].add(token)
                groups[veintype].add(token)
        for env in token.stoneclarity['ENVIRONMENT_SPEC']:
            if env.nargs() >= 2:
                spectype = 'ENVIRONMENT_SPEC_'+env.args[0]
                veintype = 'ENVIRONMENT_SPEC_'+env.args[1]
                if spectype not in groups: groups[spectype] = set()
                if veintype not in groups: groups[veintype] = set()
                groups[envtype].add(token)
                groups[veintype].add(token)
        # Handle ids and fuels
        if token.nargs() == 1:
            id = token.args[0]
            ids[id] = token
            if id in fuels:
                if 'FUEL' not in groups: groups['FUEL'] = set()
                groups['FUEL'].add(token)
    if log: log.debug('Finished building dicts! Found %d groups and %d ids.' % (len(groups), len(ids)))
    return groups, ids

# From dicts built by builddicts and given a rule, return a set of inorganics which match that rule
def getrulematches(rule, groups, ids, log=None):
    matches = set()
    if 'group' in rule:
        matchgroups = (rule['group'],) if isinstance(rule['group'], basestring) else rule['group']
        for groupname in matchgroups:
            if groupname in groups: matches = matches.union(groups[groupname])
    if 'id' in rule:
        matchids = (rule['id'],) if isinstance(rule['id'], basestring) else rule['id']
        for id in matchids:
            if id in ids: matches.add(ids[id])
    if 'filter' in rule:
        filters = (rule['filter'],) if callable(rule['filter']) else rule['filter']
        for rulefilter in filters:
            for inorganic in ids.itervalues():
                if rulefilter(inorganic): matches.add(inorganic)
    return matches
    
# Applies a list of rules to matches based on built dicts
def applyrules(rules, groups, ids, log=None):
    for rule in rules:
        if 'mutator' in rule:
            mutator = rule['mutator']
            matches = getrulematches(rule, groups, ids, log)
            if log: log.info('Applying %s rule to %d matches...' % (rule['name'] if 'name' in rule else 'unnamed', len(matches)))
            for match in matches:
                if callable(mutator):
                    mutator(match)
                else:
                    for mut in mutator: mut(match)
        else:
            if log: log.warning('Encountered %s rule with no mutators.' % rule['name'] if 'name' in rule else 'unnamed')

@pydwarf.urist(
    name = 'pineapple.stoneclarity',
    version = '1.0.0',
    author = 'Sophie Kirschner',
    description = 'Allows powerful editing of the appearances of stone, ore, and gems.',
    arguments = {
        'rules': '''By default makes all flux stone white, makes all fuel use *, makes all ore use £ unmined and * in
            stockpiles, makes cobaltite use % unmined and • in stockpiles, makes all gems use ☼. Specify an object
            other than default_rules to customize behavior, and refer to default_rules as an example of how rules are
            expected to be represented''',
        'query': '''This query is run for each inorganic found and looks for tokens that should be recognized as
            indicators that some inorganic belongs to some group. Refer to the default query for more information.''',
        'fuels': '''If left unspecified, stoneclarity will attempt to automatically detect which inorganics are fuels.
            If you know that no prior script added new inorganics which can be made into coke then you can cut down a
            on execution time by setting fuels to fuels_vanilla.'''
    }
)
def stoneclarity(dfraws, rules=default_rules, query=default_inorganics_query, fuels=None):
    if rules and len(rules):
        groups, ids = builddicts(query, dfraws, fuels if fuels else autofuels(dfraws, pydwarf.log), pydwarf.log)
        applyrules(rules, groups, ids)
        return pydwarf.success('Finished applying %d rules to %d inorganic groups and %d inorganic ids.' % (len(rules), len(groups), len(ids)))
    else:
        return pydwarf.failure('I was given no rules to follow.')









