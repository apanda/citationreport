#!/usr/bin/env python3
import sys
import requests
import json
import re
import pprint
import time
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

pp = pprint.PrettyPrinter(indent=4)
AUTHOR_URL="http://api.semanticscholar.org/v1/author/%s"
PAPER_URL = "http://api.semanticscholar.org/v1/paper/%s?include_unknown_references=true"
def main(author_id, author_name):
    files = set()
    latex_files = set()
    latex_template = open('template.tex').read()
    # First get author
    r = requests.get(AUTHOR_URL%author_id)
    author = json.loads(r.text)
    for paper in author['papers']:
        r = requests.get(PAPER_URL%paper['paperId'])
        paper_object = json.loads(r.text)
        try:
            authors = map(lambda x: x['name'], paper_object['authors'])
            if author_name not in authors:
                print("Ignoring paper ", paper_object['title'])
                continue
            fpfx = str(paper_object['title']).strip().replace(' ', '_')
            fpfx = re.sub(r'(?u)[^-\w.]', '', fpfx)
            fname = fpfx[:120] + ".bib"
            if fname in files:
                fname = fpfx[:120] + "1.bib"
                if fname in files:
                    raise("Too many things with the same name")
            files.add(fname)
            print(files)
            with open(fname, 'w') as out:
                print("Writing ", fname, len(paper_object['citations']), PAPER_URL%paper['paperId'])
                cites = []
                for cite in paper_object['citations']:
                    title = "{" + cite['title'] + "}"
                    venue = cite['venue']
                    year = str(cite['year'])
                    ID = cite['paperId']
                    authors = map(lambda x: x['name'], cite['authors'])
                    cites.append({'ENTRYTYPE': 'inproceedings', 'year': year, 'booktitle': venue, 'title': title,
                        'author': ' AND '.join(authors), 'ID': ID})
                print(len(cites))
                db = BibDatabase()
                db.entries = cites
                writer = BibTexWriter()
                out.write(writer.write(db))
            print("Done with ", fname)
            if 'authors' not in paper_object:
                authors = []
            else:
                authors = map(lambda x: x['name'], paper_object['authors'])
            ltx = latex_template.replace("[:author:]", author_name)
            ltx = ltx.replace("[:title:]", paper_object['title'])
            ltx = ltx.replace("[:authors:]", ', '.join(authors))
            ltx = ltx.replace("[:venue:]", paper_object['venue'])
            ltx = ltx.replace("[:year:]", str(paper_object['year']))
            ltx = ltx.replace("[:bibpfx:]", fname[:-4])
            tex_fn = fname[:-4] + ".tex"
            with open(tex_fn, 'w') as ltx_out:
                ltx_out.write(ltx)
            time.sleep(0.5)
        except Exception as e:
            print("Error processing ", e)
            raise
if __name__=="__main__":
    if len(sys.argv) < 3:
        print("Usage: %s authorID authorName"%sys.argv[0], file=sys.stderr)
        print("   authorId is the semantic scholar ID", file=sys.stderr)
        print("   authorName is a name to filter by", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
