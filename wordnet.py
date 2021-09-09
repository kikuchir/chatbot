import sqlite3
conn = sqlite3.connect("./wordnet/wnjpn.db",check_same_thread=False)
c = conn.cursor()
def get_synonyms(word):
  synsets = []
  word_id = 99999999
  wordid_rows = c.execute("select wordid from word where lemma = '%s'" % word)
  for wordid_row in wordid_rows:
    word_id = wordid_row[0]
  if word_id == 99999999:return synsets
  synset_rows = c.execute("select synset from sense where wordid = '%s'" % word_id)
  for synset_row in synset_rows:
    synsets.append(synset_row[0])
  synonym_list = []
  for synset in synsets:
    synonym_ids = conn.execute("select wordid from sense where (synset='%s' and wordid!=%s)" % (synset,word_id))
    for synonym_id in synonym_ids:
      synonym = conn.execute("select lemma from word where wordid=%s" % synonym_id[0])
      for row in synonym:
        synonym_list.append(row[0])
  return synonym_list
