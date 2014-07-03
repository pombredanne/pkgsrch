db315finalproj
==============

2.

Team members: Steven Griffin
Section: 315
Description: Improve upon existing package search engines like axi-cache by
             incorporating relational data and options and fuzzily searching
             through the man pages of the system.

3. Several extra features were cut due to lack of time: maintainers and
   doing statistical queries like summing or averaging various stats.
   The core functionality remains intact.
   
4. 
   Data extraction code is in init.py.
   Data processing code is in proc.py.
   Man pages were downloaded from
   http://manpages.debian.net/cgi-bin/man.cgi/help.html.
   I should have used the Jessie link, but it was too big
   and my bandwidth was getting throttled so I used the Squeeze link.
   Other data was acquired by querying the apt cache python api.
   The man pages are assembled into a Xapian database, which is queried
   and the results are fuzzily matched against the PostgreSQL database.

5.  Debian 8.0 Jessie
    PostgreSQL 9.3
    Python 2.7
    
6.
  You must have a Linux distro that uses the apt package system.
  Install dependencies:
    sudo apt-get install python-psycopg2 postgresql-9.3 postgresql-contrib
  Change to postgres user:
    sudo su postgres
  Make database:
    psql
    CREATE USER <your_name>;
    CREATE DATABASE pkgdb WITH OWNER <your_name>;
    \c pkgdb;
    CREATE EXTENSION fuzzystrmatch;
    \q
  Change back to regular user:
    exit
  You need to get the appropriate man pages now by manual download or wget.
  These are at http://manpages.debian.net/cgi-bin/man.cgi/help.html.
  Extract the tar archive from the download.
  cd into manpages/<your_debian_version>/usr/share/man/man1
  Extract the man pages with "gzip -d \*.gz" (no backslash)
  cp -r the man1 directory to man_pages in the directory of pkgsrch.py.
  Initialize databases:
    ./pkgsrch.py --init
  Run a test query:
    ./pkgsrch.py wireless gui --limit 2 --asc
  (Optional):
    Set it up as a command by aliasing or symlinking to pkgsrch.py.
  Obviously this is a bit crazy, but these steps could have been automated
  if there was more time.

  Running:
    Use ./pkgsrch.py --help:
        usage: pkgsrch.py [-h] [-v] [-i] [-l LIMIT] [--sort=alpha] [--asc]
                  [--depend DEPEND] [--priority PRIORITY] [--exact]
                  [--hide-description] [--show-man]
                  [search_term [search_term ...]]

        Search the package cache

        positional arguments:
          search_term           Term(s) to search for

        optional arguments:
          -h, --help            show this help message and exit
          -v, --version         show program's version number and exit
          -i, --init            Initialize database.
                                Overrides any other arguments.
          -l LIMIT, --limit LIMIT
                                Limit number of results
          --sort=alpha          Sort alphabetically instead of by relevance
          --asc                 Sort ascending instead of descending
          --depend DEPEND       List packages with this dependency
          --priority PRIORITY   List packages with this priority
          --exact               List packages with this exact name
          --hide-description    Don't print the description of packages
          --show-man            Print the man page of packages

7. Cursors, data extraction issues, fuzzy searching.

8. It requires a fairly painful download size and setup. If the
   data was offloaded to a server running the database and queried against,
   it might be more attractive. This would be complex because the server
   would need to support multiple separate package caches.
   The statistical queries originally planned would also benefit it.
   The input format is fairly limiting and does not provide for complex
   nested queries or anything of that sort. This could be improved with a
   more powerful input syntax.

9.

./pkgsrch.py --asc --sort=alpha --hide-description --limit 3 wireless gui
===================
Package name: cutils
Relevancy: 98%
===================
Package name: kism3d
Relevancy: 95%
===================
Package name: network-manager
Relevancy: 100%

10.

        CREATE SEQUENCE pack_id_seq;
        CREATE TABLE package (
                pack integer NOT NULL DEFAULT nextval('pack_id_seq')
                    PRIMARY KEY,
                name text,
                installed boolean
        );

        CREATE TABLE fileinfo (
                path text,
                sizeInstalled bigint,
                pack integer,
                FOREIGN KEY(pack) REFERENCES package(pack)
        );

        CREATE TABLE descriptor (
                description text,
                tag text[],
                section text,
                manpage text,
                relevancy integer,
                pack integer,
                FOREIGN KEY(pack) REFERENCES package(pack)
        );

        CREATE TABLE compatibility (
                architecture text,
                version text,
                dependencies text[],
                priority text,
                branch text,
                packageSite text,
                pack integer,
                FOREIGN KEY(pack) REFERENCES package(pack)
        );

        CREATE SEQUENCE maint_id_seq;
        CREATE TABLE maintainer (
                mid integer NOT NULL DEFAULT
                    nextval('maint_id_seq') PRIMARY KEY,
                name text,
                email text,
                homepage text
        );

        CREATE TABLE maintains (
            maint integer,
            FOREIGN KEY(maint) REFERENCES maintainer(mid),
            pack integer,
            FOREIGN KEY(pack) REFERENCES package(pack)
        );

11. All SQL code is embedded in the Python files.

12. The data used is in excess of 450 MB. A small sample has
    been preserved in the submission in man_pages. You may
    of course download it yourself from the above linked page.
