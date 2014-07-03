#!/usr/bin/env python
import psycopg2, argparse, apt, sys
from subprocess import call
from init import initializeDB
from proc import processQuery

def main(**args):
    """Main function."""
    conn = psycopg2.connect(
            #"dbname=pkgdb"
            database="pkgdb",
            port="5433"
            )

    cur = conn.cursor()
    print str(args)
    if args['init']:
        initializeDB(cur)
    else:
        processQuery(args, cur)

    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    # Command line argument handling.
    parser = argparse.ArgumentParser(
            description='Search the package cache', version='0.1')
    parser.add_argument('search_term', help='Term(s) to search for',
                         nargs='*')
    parser.add_argument('-i', '--init',
            help='Initialize database. Overrides any other arguments.',
            action="store_true")
    parser.add_argument('-l', '--limit',
            help='Limit number of results',
            type=int)
    parser.add_argument('--sort=alpha',
            help='Sort alphabetically instead of by relevance',
            action='store_const',
            const='package.name', default='descriptor.relevancy')
    parser.add_argument('--asc',
            help='Sort ascending instead of descending',
            action='store_const',
            const='ASC', default='DESC')
    parser.add_argument('--depend',
            help='List packages with this dependency')
    parser.add_argument('--priority',
            help='List packages with this priority')
    parser.add_argument('--exact',
            help='List packages with this exact name',
            action='store_true')
    parser.add_argument('--hide-description',
            help="Don't print the description of packages",
            action="store_const",
            const='', default=', descriptor.description')
    parser.add_argument('--show-man',
            help="Print the man page of packages",
            action="store_true")
    
    args = parser.parse_args()
    main(**vars(args))
