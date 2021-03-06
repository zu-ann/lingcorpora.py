from requests import get
from bs4 import BeautifulSoup
import sys
import argparse
from html import unescape
import csv
import unittest
import os

def get_results(query,corpus,page):
    """
    create a query url and get results for one page
    """
    params = {
        "corpname": corpus,
        "iquery": query,
        "fromp": page
    }
    r = get('http://maslinsky.spb.ru/bonito/run.cgi/first',params)
    return unescape(r.text)


def parse_page(page,first=False):
    """
    find results (and total number of results) in the page code
    """
    soup = BeautifulSoup(page, 'lxml')
    res = soup.find('table')
    res = res.find_all('tr')
    if first:
        num_res = int(soup.select('strong[data-num]')[0].text)
        return res, num_res
    return res


def parse_results(results,tags,corpus):
    """
    find hit and its left and right contexts
    in the extracted row of table
    """
    parsed_results = []
    for i in range(len(results)):
        lc = ' '.join([x.text.strip() for x in results[i].select('td.lc span.nott')])
        kws = results[i].select('td.kw div.token')
        final_kws = []
        for kw in kws:
            tag = kw.select('div.aline')
            tag = '; '.join([x.text.strip() for x in tag if x.text.strip()])
            if tags and tag and corpus == 'corbama-net-tonal':
                text_kw = kw.select('span.nott')[0].text.strip() +' ('+tag+')'
            else:
                text_kw = kw.select('span.nott')[0].text.strip()
            final_kws.append(text_kw)
        rc = ' '.join([x.text.strip() for x in results[i].select('td.rc span.nott')])
        parsed_results.append([lc,' '.join(final_kws),rc])
    return parsed_results


def download_all(query,num_res,corpus,tags):
    """
    get information and hits from first page and iterate until
    all hits are collected or the maximum set by user is achieved
    """
    per_page = 20
    try:
        first,total = parse_page(get_results(query,corpus,1),first=True)
    except:
        return []
    results = parse_results(first,tags,corpus)
    final_total = min(total,num_res)
    pages_to_get = len(list(range(per_page+1,final_total+1,per_page)))
    for i in range(pages_to_get):
        one_page = parse_page(get_results(query,corpus,i))
        one_res = parse_results(one_page,tags,corpus)
        results += one_res
    if len(results) > final_total:
        results = results[:final_total]
    return results


def write_results(query,results,cols):
    """
    write csv
    """
    not_allowed = '/\\?%*:|"<>'
    query = ''.join([x if x not in not_allowed else '_na_' for x in query])
    with open('bam_search_'+query+'.csv','w',encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';', quotechar='"',
                            quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        writer.writerow(cols)
        for i,x in enumerate(results):
            writer.writerow([i]+x)


def main(query,corpus='corbama-net-non-tonal',tag=False,
         n_results=10,kwic=True,write=False):
    """
    main function
    
    Args:
        query: a query to search by
        corpus: a subcorpus ('corbama-net-non-tonal' by default)
        tag: whether to provide grammatical information 
        n_results: desired number of results (10 by default)
        kwic: whether to write into file in kwic format or not
        write: whether to write into csv file or not
        
    Return:
        list of row lists and csv file is written if specified
        
    """
    results = download_all(query,n_results,corpus,tag)
    if not results:
        print ('bam_search: nothing found for "%s"' % (query))
    if kwic:
        cols = ['index','left','center','right']
    else:
        results = [[''.join(x)] for x in results]
        cols = ['index','result']
    if write:
        write_results(query,results,cols)
    return results


class TestMethods(unittest.TestCase):
    def test1(self):
        self.assertTrue(download_all(query='jamana',num_res=10,corpus='corbama-net-non-tonal',tags=False))

    def test2(self):
        r = main(query='kɔ́nɔ',corpus='corbama-net-tonal',tag=True,write=True)
        filelist = os.listdir()
        self.assertIn('bam_search_kɔ́nɔ.csv',filelist)
        os.remove('bam_search_kɔ́nɔ.csv')

        
if __name__ == '__main__':
    unittest.main()
    args = sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('query', type=str)
    parser.add_argument('corpus', type=str)
    parser.add_argument('tag', type=bool)
    parser.add_argument('n_results', type=int)
    parser.add_argument('kwic', type=bool)
    parser.add_argument('write', type=bool)
    args = parser.parse_args(args)
    main(**vars(args))
