import psycopg2, argparse, apt, sys, xapian, os
import util

def processQuery(args, cur):
    selectClause = buildSelect(args, cur)
    whereClause = buildWhere(args, cur)
    orderByClause = buildOrderBy(args, cur)
    fromClause = buildFrom(selectClause, whereClause, args, cur)
    limitClause = buildLimit(args, cur)
    buildSearchTerm(args)
    if not args['exact']:
        xapianSearch(args, cur)
    cur.execute(selectClause + fromClause + whereClause + \
            orderByClause + limitClause,
            args)
    if not args['exact']:
        zeroRelevancies(cur)

def printQuery(args, cur):
    for row in cur.fetchall():
        print '==================='
        iter = row.__iter__()
        print 'Package name: ' + iter.next()
        if args['hide_description'] is not '':
            print 'Description: ' + iter.next()
        if args['priority']:
            print 'Priority: ' + iter.next()
        if args['depend']:
            dependencies = iter.next()
            s = ''
            for d in dependencies:
                s += d + ', '
            print 'Dependencies: ' + s
        if not args['exact']:
            print 'Relevancy: ' + str(iter.next()) + '%'

def buildOrderBy(args, cur):
    orderByClause = " ORDER BY " + args['sort=alpha'] + " " + args['asc']
    return orderByClause

def buildSelect(args, cur):
    selectClause = "SELECT package.name" + args['hide_description']
    if args['priority']:
        selectClause += ', compatibility.priority'
    if args['depend']:
        selectClause += ', compatibility.dependencies'
    if not args['exact']:
        selectClause += ', descriptor.relevancy'
    return selectClause

def buildFrom(select, where, args, cur):
    fromClause = ' FROM package '
    for tn in ['fileinfo',
        'descriptor', 'compatibility',
        'maintains', 'maintainer']:
        if tn in select + where:
            fromClause += ' NATURAL JOIN ' + tn + ' '
    return fromClause

def buildWhere(args, cur):
    whereClause = ' WHERE '
    if args['exact']:
        whereClause += ' package.name = %(search_term)s AND '
    else:
        whereClause += 'descriptor.relevancy != 0 AND '
    if args['priority']:
        whereClause += ' compatibility.priority = %(priority)s AND '
    if args['depend']:
        whereClause += ' %(depend)s = ANY(compatibility.dependencies) AND '
    if whereClause == ' WHERE ':
        return ''
    # Trim last ' AND '.
    return whereClause[0:-5]

def buildLimit(args, cur):
    lim = args['limit']
    if lim is None:
        return ''
    return ' LIMIT %(limit)s '

def buildSearchTerm(args):
    term = ''
    for w in args['search_term']:
        term += ' ' + w
    args['search_term'] = term

def xapianSearch(args, cur):
    """Do a fuzzy text search on the man pages."""
    db = xapian.Database(util.getDir('man_pages'))
    enquire = xapian.Enquire(db)
    qp = xapian.QueryParser()
    stemmer = xapian.Stem("english")
    qp.set_stemmer(stemmer)
    qp.set_database(db)
    qp.set_stemming_strategy(xapian.QueryParser.STEM_SOME)
    query = qp.parse_query(args['search_term'])

    enquire.set_query(query)
    limit = args['limit']
    if limit is None:
        limit = 10
    matches = enquire.get_mset(0, limit)

    for m in matches:
        data = m.document.get_data()
        name = data.split('\n', 1)[0]
        # Fuzzy match the package name
        cur.execute("""SELECT pack FROM package WHERE 
                levenshtein(name, %s) < 3;""",
                (name,))
        packId = cur.fetchone()
        if packId is not None:
            cur.execute("""UPDATE descriptor SET relevancy = %s,
                                                 manpage = %s
                                  WHERE pack = %s""", (m.percent,
                                                       data,
                                                       packId[0]))

def zeroRelevancies(cur):
    """Set all relevancies to zero so the next search
    isn't affected."""
    cur.execute("""UPDATE descriptor SET relevancy = 0;""")
