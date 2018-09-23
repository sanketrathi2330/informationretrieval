from indexing import FormIndex
from queryOperation import FormQueryIndex

def main() :
    i = FormIndex()
    q = FormQueryIndex()
    i.createIndex()
    q.queryIndex()

if __name__== "__main__" : main()
