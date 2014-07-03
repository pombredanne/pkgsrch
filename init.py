import psycopg2, argparse, apt, sys, os, xapian
import util
from subprocess import call

def initializeDB(cur):
    """Drop tables if they already exist. Create them. Populate them."""
    dropTables(cur)
    createTables(cur)
    populateFromApt(cur)
    xapianInit()

def dropTables(cur):
    """Drop old tables in database."""
    [dropTableIfExists(tn, cur) for tn in ['package', 'fileinfo',
        'descriptor', 'compatibility',
        'maintains', 'maintainer']]
    [dropSequenceIfExists(sn, cur) for sn in ['pack_id_seq',
        'maint_id_seq']]

def createTables(cur):
    """Create tables for the database."""
    cur.execute(
            """CREATE SEQUENCE pack_id_seq;
        CREATE TABLE package (
                pack integer NOT NULL DEFAULT nextval('pack_id_seq')
                    PRIMARY KEY,
                name text,
                installed boolean
        );""")

    cur.execute(
            """CREATE TABLE fileinfo (
                path text,
                sizeInstalled bigint,
                pack integer,
                FOREIGN KEY(pack) REFERENCES package(pack)
        );""")

    cur.execute("""CREATE TABLE descriptor (
                description text,
                tag text[],
                section text,
                manpage text,
                relevancy integer,
                pack integer,
                FOREIGN KEY(pack) REFERENCES package(pack)
        );""")

    cur.execute("""CREATE TABLE compatibility (
                architecture text,
                version text,
                dependencies text[],
                priority text,
                branch text,
                packageSite text,
                pack integer,
                FOREIGN KEY(pack) REFERENCES package(pack)
        );""")

    cur.execute("""CREATE SEQUENCE maint_id_seq;
        CREATE TABLE maintainer (
                mid integer NOT NULL DEFAULT
                    nextval('maint_id_seq') PRIMARY KEY,
                name text,
                email text,
                homepage text
        );""")

    cur.execute("""CREATE TABLE maintains (
            maint integer,
            FOREIGN KEY(maint) REFERENCES maintainer(mid),
            pack integer,
            FOREIGN KEY(pack) REFERENCES package(pack)
        );""")

def tableExists(tableName, cur):
    """Return true if the table exists, false otherwise."""
    cur.execute("""SELECT EXISTS(SELECT 1 
                          FROM information_schema.tables
                          WHERE table_catalog='pkgdb' AND 
                          table_schema='public' AND
                          table_name=%s);""", (tableName,))
    return cur.fetchone()[0]

def sequenceExists(sequenceName, cur):
    """Return true if the sequence exists, false otherwise."""
    cur.execute("""SELECT EXISTS(SELECT 1 
                          FROM information_schema.sequences
                          WHERE sequence_catalog='pkgdb' AND 
                          sequence_schema='public' AND
                          sequence_name=%s);""", (sequenceName,))
    return cur.fetchone()[0]

def dropTableIfExists(tableName, cur):
    """Drop a table if it exists."""
    if tableExists(tableName, cur):
        cur.execute('DROP TABLE ' + tableName + ' CASCADE;')
        return True
    return False

def dropSequenceIfExists(seqName, cur):
    """Drop a sequence if it exists."""
    if sequenceExists(seqName, cur):
        cur.execute('DROP SEQUENCE ' + seqName + ' CASCADE;')
        return True
    return False

def populateFromApt(cur):
    """Populates the database from the apt cache."""
    cache = apt.cache.Cache()
    for i, pkg in enumerate(cache):
        if i % 20 == 0:
            writeProgress(i, len(cache), 'Populating from cache')
        insertRows(pkg, cur)

def insertRows(pkg, cur):
    cur.execute('INSERT INTO package (name) VALUES (%s)', 
            (pkg.name,))
    packId = getMax('pack', 'package', cur)
    if len(pkg.versions) == 0:
        return
    v = pkg.versions[0]
    cur.execute("""INSERT INTO fileinfo (path,
                                         sizeInstalled, pack)
                                         VALUES (%s, %s, %s)""",
                                         (v.filename, 
                                          v.installed_size, packId))

    cur.execute("""INSERT INTO descriptor (
                description,
                tag,
                section,
                manpage,
                relevancy,
                pack) VALUES (%s, %s, %s, %s, %s, %s)""", 
                (v.raw_description, ['k', '...'], v.section, 0, 0, 
                 packId))
    dependencies = map(lambda d: d.or_dependencies[0].name,
                       v.dependencies)
    cur.execute("""INSERT INTO compatibility (
                architecture,
                version,
                dependencies,
                priority,
                branch,
                packageSite,
                pack) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (v.architecture, v.version, dependencies,
                 v.priority, 0, v.homepage, packId))

    cur.execute("""INSERT INTO maintainer (name, email, homepage)
                   VALUES (%s, %s, %s)""", (0, 0, 0))
    maintId = getMax('mid', 'maintainer', cur)
    cur.execute("""INSERT INTO maintains (maint, pack)
                   VALUES (%s, %s)""", (maintId, packId))
    

def getMax(col, rel, cur):
    """Returns the max of the given column from the relation."""
    cur.execute('SELECT MAX(' + col + ') FROM ' + rel)
    return cur.fetchone()[0]

def writeProgress(current, total, message):
    """Writes a progress percentage to stdout."""
    sys.stdout.write(message + ": %3.2f%%   \r" \
            % (float(current) / total * 100))
    sys.stdout.flush()

def xapianInit():
    manPath = util.getDir('man_pages')
    database = xapian.WritableDatabase(manPath,
            xapian.DB_CREATE_OR_OVERWRITE)
    indexer = xapian.TermGenerator()
    indexer.set_stemmer(xapian.Stem("english"))
    files = os.listdir(manPath)
    for index, f in enumerate(files):
        writeProgress(index, len(files), 'Populating man page db')
        if f.endswith(".1"):
            try:
                with open(os.path.join(manPath, f), 'r+b') as manFile:
                    stringifiedFile = manFile.read()
                    doc = xapian.Document()
                    doc.set_data(f.replace(".1", "") + '\n' + \
                            stringifiedFile)
                    indexer.set_document(doc)
                    indexer.index_text(stringifiedFile)
                    database.add_document(doc)
            except Exception as e:
                print 'Failed to index ' + f + ': ' + \
                        e.args[len(e.args) - 1]

