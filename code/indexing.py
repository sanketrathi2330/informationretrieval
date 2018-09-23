import os
import re
from porterStemmer import PorterStemmer
from collections import defaultdict
from array import array
import gc
import math

stemmer=PorterStemmer()

class FormIndex:

    def __init__(self):
        self.index=defaultdict(list)    #the inverted index
        self.titleIndex={}
        self.tf=defaultdict(list)          #term frequencies of terms in documents
                                                    #documents in the same order as in the main index
        self.df=defaultdict(int)         #document frequencies of terms in the corpus
        self.numDocuments=0

    
    def getStopwords(self):
        '''get stopwords from the stopwords file'''
        f=open('stopwords.dat', 'r')
        stopwords=[line.rstrip() for line in f]
        self.sw=dict.fromkeys(stopwords)
        f.close()
        

    def getTerms(self, line):
        '''given a stream of text, get the terms from the text'''
        line=line.lower()
        line=re.sub(r'[^a-z0-9 ]',' ',line) #put spaces instead of non-alphanumeric characters
        line=line.split()
        line=[x for x in line if x not in self.sw]  #eliminate the stopwords
        line=[ stemmer.stem(word, 0, len(word)-1) for word in line]
        return line


    def parseCollection(self):
        ''' returns the id, title and text of the next page in the collection '''
        doc=[]
        for line in self.collFile:
            if line=='<end>\n':
                break
            doc.append(line)
        
        curPage=''.join(doc)
        pageid=re.search('<id>(.*?)</id>', curPage, re.DOTALL)
        pagetitle=re.search('<title>(.*?)</title>', curPage, re.DOTALL)
        pagetext=re.search('<text>(.*?)</text>', curPage, re.DOTALL)
        
        if pageid==None or pagetitle==None or pagetext==None:
            return {}

        d={}
        d['id']=pageid.group(1)
        d['title']=pagetitle.group(1)
        d['text']=pagetext.group(1)

        return d


    def writeIndexToFile(self):
        '''write the index to the file'''
        #write main inverted index
        f=open('indexFile', 'w')
        #first line is the number of documents
        print >>f, self.numDocuments
        count = 0
        self.numDocuments=float(self.numDocuments)
        for term in self.index.iterkeys():
            postinglist=[]
            for p in self.index[term]:
                docID=p[0]
                positions=p[1]
                postinglist.append(':'.join([str(docID) ,','.join(map(str,positions))])) 
            #print data
            postingData=';'.join(postinglist)
            tfData=','.join(map(str,self.tf[term]))
            idfData='%.4f' % math.log10(self.numDocuments/self.df[term])
            print >> f, '|'.join((term, postingData, tfData, idfData))
        f.close()
        
        #write title index
        f=open('titleIndexFile','w')
        for pageid, title in self.titleIndex.iteritems():
            print >> f, pageid, title
        f.close()
    
    def collectionFile(self):
        #gets the collection file input from the user
        path = os.getcwd()
        while 1:
            a = raw_input('DirectoryName or Filename (D/F):')
            if a=='D' or a =='d':
                file_list = []
                path = path+'/'+raw_input()
                for file_name in os.listdir(path):
                    file_list.append(file_name)
                break
            elif a=='F' or a=='f':
                file_list = raw_input("Names of the Files:").strip().split()
                break
            else :
                continue
            
        self.numDocuments = len(file_list)
        collFile = open('random','w')              #writing all the data in one single file
        for num, file in enumerate(file_list) :
            f = open(path+'/'+file)
            buffersize = 50000                     #breaking file in bunches before copying
            buffer = f.read(buffersize)
            collFile.write('<start>'+'\n')
            collFile.write('<id>'+str(num+1)+'</id>'+'\n')
            collFile.write('<title>'+str(file)+'</title>'+'\n')
            collFile.write('<text>'+'\n')
            while len(buffer) :
                collFile.write(buffer)
                buffer = f.read(buffersize)
            collFile.write('</text>'+'\n')
            collFile.write('<end>'+'\n')
            f.close()
        collFile.close()
        

    def createIndex(self):
        '''main of the program, creates the index'''
        self.collectionFile()
        self.collFile=open('random','r')
        self.getStopwords()
                
        #bug in python garbage collector!
        #appending to list becomes O(N) instead of O(1) as the size grows if gc is enabled.
        gc.disable()
        
        pagedict={}
        pagedict=self.parseCollection()
        #main loop creating the index
        while pagedict != {}:                    
            lines='\n'.join((pagedict['title'],pagedict['text']))
            pageid=int(pagedict['id'])
            terms=self.getTerms(lines)
            
            self.titleIndex[pagedict['id']]=pagedict['title']
            
            #build the index for the current page
            termdictPage={}
            for position, term in enumerate(terms):
                try:
                    termdictPage[term][1].append(position)
                except:
                    termdictPage[term]=[pageid, array('I',[position])]
        
            
            #calculate the tf and df weights
            for term, posting in termdictPage.iteritems():
                value = math.log10(len(posting[1]))+1
                self.tf[term].append('%.4f' % (value))
                self.df[term]+=1
            
            #merge the current page index with the main index
            for termPage, postingPage in termdictPage.iteritems():
                self.index[termPage].append(postingPage)
            
            pagedict=self.parseCollection()

        self.collFile.close()
        gc.enable()
            
        self.writeIndexToFile()
        os.remove('random')            #removes the created file
    
if __name__ == "__main__":
    c = FormIndex()
    c.createIndex()
