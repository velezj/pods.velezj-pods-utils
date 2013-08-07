#!/usr/bin/env python


from functools import reduce
import sys
import os
import subprocess


DEBUG=False 

def toposort(data):
    """Dependencies are expressed as a dictionary whose keys are items
and whose values are a set of dependent items. Output is a list of
sets in topological order. The first set consists of items with no
dependences, each subsequent set consists of items that depend upon
items in the preceeding sets.

>>> print '\\n'.join(repr(sorted(x)) for x in toposort2({
...     2: set([11]),
...     9: set([11,8]),
...     10: set([11,3]),
...     11: set([7,5]),
...     8: set([7,3]),
...     }) )
[3, 5, 7]
[8, 11]
[2, 9, 10]

"""

    # FROM: http://code.activestate.com/recipes/578272-topological-sort/

    # Ignore self dependencies.
    for k, v in data.items():
        v.discard(k)

    # Find all items that don't depend on anything.
    extra_items_in_deps = reduce(set.union, data.itervalues()) - set(data.iterkeys())

    # Add empty dependences where needed
    data.update({item:set() for item in extra_items_in_deps})
    while True:
        ordered = set(item for item, dep in data.iteritems() if not dep)
        if not ordered:
            break
        yield ordered
        data = {item: (dep - ordered)
                for item, dep in data.iteritems()
                    if item not in ordered}
    assert not data, "Cyclic dependencies exist among these items:\n%s" % '\n'.join(repr(x) for x in data.iteritems())




_known_library_source_map = {}
def _load_library_source_map( filename_set ):
    for fn in filename_set:
        with open( fn ) as f:
            for line in f:
                lib,fetch_command,make_command = line.split("@@", 2 )
                lib = lib.strip()
                fetch_command = fetch_command.strip()
                make_command = make_command.strip()
                if DEBUG:
                    print "** " + lib
                    print "      FETCH: " + fetch_command
                    print "      MAKE : " + make_command
                _known_library_source_map[ lib ] = (fetch_command,make_command)



def try_to_find_pc_filename( lib ):

    if DEBUG:
        print "  ! trying for raw .pc file"

    # The first thing to do is update the local database
    try:
        subprocess.check_call( ["updatedb", "-l", "0", "-o", ".local-mlocate-db", "-U", "/home/" ] )
        if DEBUG:
            print "  % updated local mlocate databse"
    except:
        pass

    try:
        output = subprocess.check_output( ["locate", "--database", ".local-mlocate-db", "--database", "", lib + ".pc" ] )
        return output.split("\n")[0].strip()
    except:
        # if DEBUG:
        #     print "~~ WARNING: falling back to find backed, which is SLOW!"
        # try:
        #     output = subprocess.check_output( ["find", "/", "-iname", lib + ".pc"] )
        #     return output
        # except:
        #     return None
        return None
    return None


def fetch_lib( lib ):
    
    # try to find and fetch this library
    if lib not in _known_library_source_map:
        raise Exception("Unknown lib: " + lib + " in source map, cannot auto-fetch!")
        
    fetch_com,make_com = _known_library_source_map[lib]
    print "   .. fetching: " + fetch_com
    #subprocess.check_call( fetch_com, shell=True )
    os.system( fetch_com )
    print "   .. making  : " + make_com
    #subprocess.check_call( make_com, shell=True )
    os.system( make_com )
    
    # if not lib_exists( lib ):
    #     raise Exception( "Fetch of " + lib + " FAILED: using mapping: " + str( (fetch_com,make_com) ) )


def lib_exists( lib ):
    res = subprocess.call( ["pkg-config", "--exists", lib ] )
    return (res == 0 )


def get_direct_dependencies( lib ):

    if DEBUG:
        print "    -- " + lib

    req = []

    try:
        output = subprocess.check_output( ["pkg-config", "--print-requires", lib ] )
        #output_priv = subprocess.check_output( ["pkg-config", "--print-requires-private", lib ] )
    
        # parse output
        for line in output.split( "\n" ):
            l = line.strip()
            if len(l) > 0:
                req.append( line.strip() )
    except:
        
        # Ok, we were unable to get the dependencies using hte pkg-config
        # program, but this *could* be because we have a missing
        # dependency and pkg-config only succeed if the entire chain
        # is known to it, so let us try to find the .pc file itself
        # and get it's top-level dependencies
        pc_filename = try_to_find_pc_filename( lib )
        if pc_filename is not None:
            
            # at least we found the pc file, parse it :-(
            with open( pc_filename ) as f:
                for line in f:
                    line = line.strip()
                    if ":" in line:
                        toks = line.split( ":" )
                        if toks[0] == "Requires":
                            toks = toks[1].split( " " )
                            skip_next = False
                            for tt in toks:
                                if skip_next:
                                    skip_next = False
                                    continue
                                t = tt.strip()
                                if len(t) < 1:
                                    continue
                                if t == ">" or t == ">=" or t == "<" or t == "<=" or t == "=":
                                    skip_next = True
                                    continue
                                req.append( t )
        
    return req
        


def buildup_deps( libs, fetch_if_needed=True ):
    
    deps = {}
    lib_set = set(libs)
    
    while len(lib_set) > 0:
        lib = lib_set.pop()
        if len(lib) < 1:
            continue

        if not lib_exists(lib):
            if fetch_if_needed:
                fetch_lib( lib )
            else:
                raise Exception("Lib " + lib + " cannot be found using pkg-config!")

        dep_1 = get_direct_dependencies( lib )
        lib_set |= set(dep_1)
        deps[ lib ] = set(dep_1)

    return deps


if __name__ == "__main__":


    # load the know source mappings
    _load_library_source_map( set(["library-source-map.txt"]) )
    
    # grab arguments which are *not* flags (pkg-config is nice in that
    # there are no non-flag value arguments: thigns either have -- in front
    # or are a library we are querying about
    libs = []
    wanted_orderings = None
    for arg in sys.argv[1:]:
        if arg[0:2] != "--":
            libs.append( arg )
        if arg == "--debug-deps" :
            DEBUG=True
            sys.argv.remove( arg )
        if arg.startswith("--rebuild-ordering"):
            wanted_orderings = []
            with open( arg.split("=")[1].strip() ) as f:
                for line in f:
                    line_s = line.strip()
                    if len(line_s) < 1 or line_s.startswith("#"):
                        continue
                    wanted_orderings.append( line_s )
            wanted_orderings = set( wanted_orderings )
            sys.argv.remove(arg)
        if arg == "--print-requires" or arg == "--print-requires-private":
            
            # we are done, pass through and exit
            #print "passing throught!"
            res = subprocess.call( ["pkg-config"] + sys.argv[1:] )
            exit(res)

    # Ok, check if we have those libraries (using pkg-config itself)
    if DEBUG:
        print "LIBS: " + str(libs)
    
    # ok, build up depedencies using these libs
    deps = buildup_deps( libs )
    if DEBUG:
        print "FULL DEPS: " + str(deps)
    
    # compute topological ordering of the dependencies
    if DEBUG:
        print '\n'.join(repr(sorted(x)) for x in toposort(deps))
    
    # if we asked for it, print the reordered buildset as
    # per dependency information
    if wanted_orderings is not None:
        tps = toposort( deps )
        ordering = []
        for level in tps:
            if not wanted_orderings.isdisjoint( level ):
                ordering += [ x for x in ( wanted_orderings & level ) ]
        for o in ordering:
            print o
    
    
    # pass through and return
    #print "passing throught!"
    res = subprocess.call( ["pkg-config"] + sys.argv[1:] )
    exit(res)
    

