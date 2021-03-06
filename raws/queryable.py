# vim:fileencoding=UTF-8

import inspect
from filters import *



class rawsqueryable:
    '''Classes which contain raws tokens should inherit from this in order to provide querying functionality.'''
    
    query_tokeniter_docstring = '''
        tokeniter: The query runs along this iterable until either a filter has hit
            its limit or the tokens have run out.'''
    
    quick_query_args_docstring = '''
        %s
        pretty: Convenience argument which acts as a substitute for directly
            assigning a filter's exact_value and exact_args arguments. Some methods
            also accept an until_pretty argument which acts as a substitute for
            until_exact_value and until_exact_args.
        **kwargs: If no tokeniter is specified, then arguments which correspond to
            named arguments of the object's tokens method will be passed to that
            method. All other arguments will be passed to the appropriate filters,
            and for accepted arguments you should take a look at the rawstokenfilter
            constructor's docstring. Some quick query methods support arguments
            prepended with 'until_' to distinguish tokens that should be matched
            from tokens that should terminate the query. (These methods are getuntil,
            getlastuntil, and alluntil. The arguments for the until method should be
            named normally.)
    ''' % query_tokeniter_docstring
    
    def __getitem__(self, pretty): return self.get(pretty=pretty)
    def __iter__(self): return self.tokens()
    def __contains__(self, pretty): return self.get(pretty=pretty) is not None
    
    def query(self, filters, tokeniter=None, **kwargs):
        '''Executes a query on some iterable containing tokens.
        
        filters: A dict or other iterable containing rawstokenfilter-like objects.
        **kwargs: If tokeniter is not given, then the object's token method will be
            called with these arguments and used instead.
        %s
        ''' % rawsqueryable.query_tokeniter_docstring
        
        if tokeniter is None: tokeniter = self.tokens(**kwargs)
        filteriter = (filters.itervalues() if isinstance(filters, dict) else filters)
        limit = False
        for filter in filteriter: filter.result = rawstokenlist()
        for token in tokeniter:
            for filter in filteriter:
                if (not filter.limit) or len(filter.result) < filter.limit:
                    if filter.match(token): filter.result.append(token)
                    if filter.limit_terminates and len(filter.result) == filter.limit: limit = True; break
            if limit: break
        return filters
        
    def get(self, pretty=None, tokeniter=None, **kwargs):
        '''Get the first matching token.
        
        %s
        
        Example usage:
            >>> print df.get(exact_value='TRANSLATION')
            [TRANSLATION:HUMAN]
            >>> print df.get(exact_args=['6', '0', '1'])
            [PICKED_COLOR:6:0:1]
            >>> bear = df.get(match_token=raws.token('CREATURE:BEAR_GRIZZLY'))
            >>> print bear
            [CREATURE:BEAR_GRIZZLY]
            >>> print bear.get(exact_value='DESCRIPTION')
            [DESCRIPTION:A huge brown creature found in temperate woodland.  It is known for its ferocious attack, usually when it or its young are threatened.]
            >>> print bear.get(exact_value='CREATURE')
            [CREATURE:BEAR_BLACK]
        ''' % rawsqueryable.quick_query_args_docstring
        
        filter_args, tokens_args = self.argstokens(tokeniter, kwargs)
        filters = (
            rawstokenfilter(pretty=pretty, limit=1, **filter_args)
        ,)
        result = self.query(filters, tokeniter, **tokens_args)[0].result
        return result[0] if result and len(result) else None
    
    def getlast(self, pretty=None, tokeniter=None, **kwargs):
        '''Get the last matching token.
        
        %s
        
        Example usage:
            >>> dwarven = df['language_DWARF'].get('TRANSLATION:DWARF')
            >>> print dwarven.getlast('T_WORD')
            [T_WORD:PRACTICE:mubun]
        ''' % rawsqueryable.quick_query_args_docstring
        
        filter_args, tokens_args = self.argstokens(tokeniter, kwargs)
        filters = (
            rawstokenfilter(pretty=pretty, **filter_args)
        ,)
        result = self.query(filters, tokeniter, **tokens_args)[0].result
        return result[-1] if result and len(result) else None
    
    def all(self, pretty=None, tokeniter=None, **kwargs):
        '''Get a list of all matching tokens.
        
        %s
        
        Example usage:
            >>> dwarven = df['language_DWARF'].get('TRANSLATION:DWARF')
            >>> print dwarven.all(exact_value='T_WORD', re_args=['CR.*Y', None])
            [T_WORD:CRAZY:d�besh]
                [T_WORD:CREEPY:innok]
                [T_WORD:CRUCIFY:memrut]
                [T_WORD:CRY:cagith]
                [T_WORD:CRYPT:momuz]
                [T_WORD:CRYSTAL:zas]
            >>> intelligence = df.all('INTELLIGENT')
            >>> print len(intelligence)
            6
            >>> print [str(token.get('CREATURE', reverse=True)) for token in intelligence]
            ['[CREATURE:DWARF]', '[CREATURE:HUMAN]', '[CREATURE:ELF]', '[CREATURE:GOBLIN]', '[CREATURE:FAIRY]', '[CREATURE:PIXIE]']
        ''' % rawsqueryable.quick_query_args_docstring
        
        filter_args, tokens_args = self.argstokens(tokeniter, kwargs)
        filters = (
            rawstokenfilter(pretty=pretty, **filter_args)
        ,)
        return self.query(filters, tokeniter, **tokens_args)[0].result
    
    def until(self, pretty=None, tokeniter=None, **kwargs):
        '''Get a list of all tokens up to a match.
        
        %s
        
        Example usage:
            >>> hematite = df.getobj('INORGANIC:HEMATITE')
            >>> print hematite.until('INORGANIC')
            [USE_MATERIAL_TEMPLATE:STONE_TEMPLATE]
            [STATE_NAME_ADJ:ALL_SOLID:hematite][DISPLAY_COLOR:4:7:0][TILE:156]
            [ENVIRONMENT:SEDIMENTARY:VEIN:100]
            [ENVIRONMENT:IGNEOUS_EXTRUSIVE:VEIN:100]
            [ITEM_SYMBOL:'*']
            [METAL_ORE:IRON:100]
            [SOLID_DENSITY:5260]
            [MATERIAL_VALUE:8]
            [IS_STONE]
            [MELTING_POINT:12736]
            >>> print hematite.until('ENVIRONMENT')
            [USE_MATERIAL_TEMPLATE:STONE_TEMPLATE]
            [STATE_NAME_ADJ:ALL_SOLID:hematite][DISPLAY_COLOR:4:7:0][TILE:156]
        ''' % rawsqueryable.quick_query_args_docstring
        
        filter_args, tokens_args = self.argstokens(tokeniter, kwargs)
        filters = (
            rawstokenfilter(pretty=pretty, limit=1, **filter_args),
            rawstokenfilter()
        )
        return self.query(filters, tokeniter, **tokens_args)[1].result
        
    def getuntil(self, pretty=None, until=None, tokeniter=None, **kwargs):
        '''Get the first matching token, but abort when a token matching arguments prepended with 'until_' is encountered.
        
        %s
        
        Example usage:
            >>> hematite = df.getobj('INORGANIC:HEMATITE')
            >>> print hematite.get('METAL_ORE:GOLD:100')
            [METAL_ORE:GOLD:100]
            >>> print hematite.getuntil('METAL_ORE:GOLD:100', 'INORGANIC')
            None
        ''' % rawsqueryable.quick_query_args_docstring
        
        filter_args, tokens_args = self.argstokens(tokeniter, kwargs)
        until_args, condition_args = self.argsuntil(filter_args)
        filters = (
            rawstokenfilter(pretty=until, limit=1, **until_args),
            rawstokenfilter(pretty=pretty, limit=1, **condition_args)
        )
        result = self.query(filters, tokeniter, **tokens_args)[1].result
        return result[0] if result and len(result) else None
    
    def getlastuntil(self, pretty=None, until=None, tokeniter=None, **kwargs):
        '''Get the last matching token, up until a token matching arguments prepended with 'until_' is encountered.
        
        %s
        
        Example usage:
            >>> hematite = df.getobj('INORGANIC:HEMATITE')
            >>> print hematite.getlast('STATE_NAME_ADJ')
            [STATE_NAME_ADJ:ALL_SOLID:slade]
            >>> print hematite.getlastuntil('STATE_NAME_ADJ', 'INORGANIC')
            [STATE_NAME_ADJ:ALL_SOLID:hematite]
        ''' % rawsqueryable.quick_query_args_docstring
        
        filter_args, tokens_args = self.argstokens(tokeniter, kwargs)
        until_args, condition_args = self.argsuntil(filter_args)
        filters = (
            rawstokenfilter(pretty=until, limit=1, **until_args),
            rawstokenfilter(pretty=pretty, **condition_args)
        )
        result = self.query(filters, tokeniter, **tokens_args)[1].result
        return result[-1] if result and len(result) else None
     
    def alluntil(self, pretty=None, until=None, tokeniter=None, **kwargs):
        '''Get a list of all matching tokens, but abort when a token matching
        arguments prepended with 'until_' is encountered.
        
        %s
        
        Example usage:
            >>> dwarf = df.getobj('CREATURE:DWARF')
            >>> print [str(token) for token in dwarf.all('INTELLIGENT')] # Gets all INTELLIGENT tokens following CREATURE:DWARF, including those belonging to other creatures
            ['[INTELLIGENT]', '[INTELLIGENT]', '[INTELLIGENT]', '[INTELLIGENT]', '[INTELLIGENT]', '[INTELLIGENT]']
            >>> print [str(token) for token in dwarf.alluntil('INTELLIGENT', 'CREATURE')] # Gets only the dwarf's INTELLIGENT token
            ['[INTELLIGENT]']
            >>> print [str(token) for token in dwarf.alluntil('INTELLIGENT', 'CREATURE:GOBLIN')]
            ['[INTELLIGENT]', '[INTELLIGENT]', '[INTELLIGENT]']
        ''' % rawsqueryable.quick_query_args_docstring
        
        filter_args, tokens_args = self.argstokens(tokeniter, kwargs)
        until_args, condition_args = self.argsuntil(filter_args)
        filters = (
            rawstokenfilter(pretty=until, limit=1, **until_args),
            rawstokenfilter(pretty=pretty, **condition_args)
        )
        return self.query(filters, tokeniter, **tokens_args)[1].result
    
    def getprop(self, pretty=None, **kwargs):
        '''Gets the first token matching the arguments, but stops at the next
        token with the same value as this one. Should be sufficient in almost
        all cases to get a token representing a property of an object, when
        this method is called for a token representing an object. **kwargs
        are passed to the getuntil method.
        
        Example usage:
            >>> iron = df.getobj('INORGANIC:IRON')
            >>> print iron.get('WAFERS') # Gets the WAFERS token that's a property of adamantite
            [WAFERS]
            >>> print iron.getprop('WAFERS') # Stops at the next INORGANIC token, doesn't pick up adamantine's WAFERS token
            None
        '''
        
        until_exact_value, until_re_value, until_value_in = self.argsprops()
        return self.getuntil(pretty=pretty, until_exact_value=until_exact_value, until_re_value=until_re_value, until_value_in=until_value_in, **kwargs)
        
    def getlastprop(self, pretty=None, **kwargs):
        '''Gets the last token matching the arguments, but stops at the next
        token with the same value as this one. Should be sufficient in almost
        all cases to get a token representing a property of an object, when
        this method is called for a token representing an object. **kwargs
        are passed to the getlastuntil method.
        
        Example usage:
            >>> iron = df.getobj('INORGANIC:IRON')
            >>> print iron.getlast(re_value='ITEMS_.+') # Gets the property of adamantite, the last ITEMS_ token in the file
            [ITEMS_SOFT]
            >>> print iron.getlastprop(re_value='ITEMS_.+') # Gets the last ITEMS_ token which belongs to iron
            [ITEMS_SCALED]
        '''
        
        until_exact_value, until_re_value, until_value_in = self.argsprops()
        return self.getlastuntil(pretty=pretty, until_exact_value=until_exact_value, until_re_value=until_re_value, until_value_in=until_value_in, **kwargs)
            
    def allprop(self, pretty=None, **kwargs):
        '''Gets the all tokens matching the arguments, but stops at the next
        token with the same value as this one. Should be sufficient in almost
        all cases to get a token representing a property of an object, when
        this method is called for a token representing an object. **kwargs are
        passed to the alluntil method.
        
        Example usage:
            >>> hematite = df.getobj('INORGANIC:HEMATITE')
            >>> print len(hematite.all('ENVIRONMENT')) # Gets all ENVIRONMENT tokens following hematite
            38
            >>> print hematite.allprop('ENVIRONMENT') # Gets only the ENVIRONMENT tokens belonging to hematite
            [ENVIRONMENT:SEDIMENTARY:VEIN:100]
            [ENVIRONMENT:IGNEOUS_EXTRUSIVE:VEIN:100]
        '''
        
        until_exact_value, until_re_value, until_value_in = self.argsprops()
        return self.alluntil(pretty=pretty, until_exact_value=until_exact_value, until_re_value=until_re_value, until_value_in=until_value_in, **kwargs)
            
    def propdict(self, always_list=True, value_keys=True, full_keys=True, **kwargs):
        '''Returns a dictionary with token values mapped as keys to the tokens
        themselves. If always_list is True then every item in the dict will be
        a list. If it's False then items in the dict where only one token was
        found will be given as individual rawstoken instances rather than as
        lists. **kwargs are passed to the alluntil method.
        
        Example usage:
            >>> hematite = df.getobj('INORGANIC:HEMATITE')
            >>> props = hematite.propdict()
            >>> print props.get('ENVIRONMENT')
            [
            [ENVIRONMENT:SEDIMENTARY:VEIN:100],
            [ENVIRONMENT:IGNEOUS_EXTRUSIVE:VEIN:100]]
            >>> print props.get('IS_STONE')
            [
            [IS_STONE]]
            >>> print props.get('TILE:156')
            [[TILE:156]]
        '''
        
        until_exact_value, until_re_value, until_value_in = self.argsprops()
        props = self.alluntil(until_exact_value=until_exact_value, until_re_value=until_re_value, until_value_in=until_value_in, **kwargs)
        pdict = {}
        for prop in props:
            for key in (prop.value if value_keys else None, str(prop)[1:-1] if full_keys else None):
                if key is not None:
                    if key not in pdict:
                        if always_list:
                            pdict[key] = [prop]
                        else:
                            pdict[key] = prop
                    elif prop not in pdict[key]:
                        if isinstance(pdict[key], list):
                            pdict[key].append(prop)
                        else:
                            pdict[key] = [prop, pdict[key]]
        return pdict
        
    def argsuntil(self, kwargs):
        # Utility function for handling arguments of getuntil and alluntil methods
        until_args, condition_args = {}, {}
        for arg, value in kwargs.iteritems():
            if arg.startswith('until_'):
                until_args[arg[6:]] = value
            else:
                condition_args[arg] = value
        return until_args, condition_args
        
    def argstokens(self, tokeniter, kwargs):
        # Utility function for separating arguments to pass on to a tokens iterator from arguments to pass to filters
        if tokeniter is None and hasattr(self, 'tokens'):
            filter_args, tokens_args = {}, {}
            args = inspect.getargspec(self.tokens)[0]
            for argname, argvalue in kwargs.iteritems():
                (tokens_args if argname in args else filter_args)[argname] = argvalue
            return filter_args, tokens_args
        else:
            return kwargs, {}
            
    def argsprops(self):
        # Utility function for handling arguments of getprop, allprop, and propdict methods
        until_exact_value = None
        until_re_value = None
        until_value_in = None
        if self.value.startswith('ITEM_'):
            until_re_value = 'ITEM_.+'
        elif self.value == 'WORD' or self.value == 'SYMBOL':
            until_value_in = ('WORD', 'SYMBOL')
        else:
            until_exact_value = self.value
        return until_exact_value, until_re_value, until_value_in



class rawsqueryable_obj(rawsqueryable):
    def __init__(self):
        self.files = None
    
    def getobjheadername(self, type):
        # Utility function fit for handling objects as of 0.40.24
        if type in ('WORD', 'SYMBOL', 'TRANSLATION'):
            return ('LANGUAGE',)
        elif type.startswith('ITEM_'):
            return ('ITEM',)
        elif type == 'COLOR' or type == 'SHAPE':
            return ('DESCRIPTOR', 'DESCRIPTOR_%s' % type)
        elif type == 'COLOR_PATTERN':
            return ('DESCRIPTOR_PATTERN',)
        elif type.startswith('MATGLOSS_'):
            return ('MATGLOSS',)
        elif type in ('TILE_PAGE', 'CREATURE_GRAPHICS'):
            type = ('GRAPHICS',)
        else:
            return type
    
    def getobjheaders(self, type):
        '''Gets OBJECT:X tokens where X is type. Is also prepared for special cases
        like type=ITEM_PANTS matching OBJECT:ITEM. Current as of DF version 0.40.24.'''
        
        match_types = self.getobjheadername(type)
        results = []
        for rfile in self.files.itervalues():
            root = rfile.root()
            if root and root.value == 'OBJECT' and root.nargs() == 1 and root.args[0] in match_types:
                results.append(root)
        return results
    
    def getobj(self, pretty=None, type=None, exact_id=None):
        '''Get the first object token matching a given type and id. (If there's more 
            than one result for any given query then I'm afraid you've done something
            silly with your raws.) This method should work properly with things like
            CREATURE:X tokens showing up in entity_default.'''
            
        type, exact_id = rawsqueryable_obj.objpretty(pretty, type, exact_id)
        for objecttoken in self.getobjheaders(type):
            obj = objecttoken.get(exact_value=type, exact_args=(exact_id,))
            if obj: return obj
        return None
        
    def allobj(self, pretty=None, type=None, exact_id=None, re_id=None, id_in=None):
        '''Gets all objects matching a given type and optional id or id regex.'''
        
        if re_id and id_in: raise ValueError
        type, exact_id = rawsqueryable_obj.objpretty(pretty, type, exact_id)
        results = []
        for objecttoken in self.getobjheaders(type):
            for result in objecttoken.all(
                exact_value=type, exact_args=(exact_id,) if exact_id else None,
                re_args=(re_id,) if re_id else (('|'.join(id_in),) if id_in else None),
                args_count=1
            ):
                results.append(result)
        return results
        
    def objdict(self, *args, **kwargs):
        return {token.args[0]: token for token in self.allobj(*args, **kwargs)}
        
    @staticmethod
    def objpretty(pretty, type, id):
        # Utility method for handling getobj/allobj arguments.
        if pretty is not None:
            if ':' in pretty:
                parts = pretty.split(':')
                if len(parts) != 2: raise ValueError
                return parts[0], parts[1]
            elif type is None:
                return pretty, id
            elif id is None:
                return pretty, type
        else:
            return type, id



class rawstokenlist(list, rawsqueryable):
    '''Extends builtin list with token querying functionality.'''
    
    def tokens(self, range=None, include_self=False, reverse=False):
        if include_self: raise ValueError
        for i in xrange(self.__len__()-1, -1, -1) if reverse else xrange(0, self.__len__()):
            if range is not None and range <= count: break
            yield self.__getitem__(i)
            
    def __str__(self):
        return ''.join([repr(token) for token in self]).strip()


