import requests
import unicodedata
import re
import operator
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys

class JobScraper:
    base_job_url = 'http://www.indeed.com/rc/clk?jk=%s'
    base_search_url = 'http://www.indeed.com/jobs?q=software+developer&l=%s&start=%s'
    page_limit = 20

    def __init__(self, locations):
        self.locations = locations
        self.job_map = {}
        self.terms_by_city = {}
        self.search()

    # If the amount of pages attempted to be scraped is larger than the actual amount
    # of job pages, indeed will start repeating results so we have to check for this explicitly
    def repeated_results(self):
        # There can't be duplicate pages if we have only scrapped 1 page
        if len(self.search_results) < 2:
            return False
        else:
            if self.search_results[0] == self.search_results[1]:
                self.search_results.pop(0)
                return True
            else:
                self.search_results.pop(0)
                return False

    def get_joblinks_from_search(self):
        job_links = []
       
        for line in self.current_page.splitlines():
       
            if "jobmap[" in line and "{jk:" in line:
                job_id = re.findall('\'([^\']*)\'', line)[0]
                job_links.append(self.base_job_url % job_id)
        
        return job_links

    def cleanse_text(self, job_site):
        soup_obj = BeautifulSoup(job_site, "html.parser")

        for script in soup_obj(["script", "style"]):
            script.extract()

        text = soup_obj.get_text()
        lines = (line.strip() for line in text.splitlines())

        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

        # Get rid of all blank lines and ends of line
        text = ''.join(chunk + ' ' for chunk in chunks if chunk).encode('utf-8')
        try:
            text = text.decode('unicode_escape').encode('ascii', 'ignore')
        except:
            print "Unicode issue"
            return

        # Get rid of anything thats not a word
        text = re.sub("[^a-zA-Z.+3]"," ", text)
        text = text.lower().split()

        stop_words = set(stopwords.words("english"))
        terms = [w for w in text if not w in stop_words]
        terms = list(set(terms))

        return terms

    def get_job_data(self):
        i = 0
        for city, job_links in self.job_map.iteritems():
            term_count = {}

            for job in job_links:
                try:
                    r = requests.get(job)
            
                    if r.status_code == 200:
                        print "Just scraped page %d" % i
                        i += 1
                        relevant_words = self.cleanse_text(r.text)
                        try:
                            for term in relevant_words:
                
                                if term in term_count:
                                    term_count[term] += 1
                                else:
                                    term_count[term] = 1

                        except TypeError, te:
                            print relevant_words, 'is not iterable'
                    else:
                        print "Job link doesn't work"
                        pass
                except requests.exceptions.RequestException as e:
                    print e

            self.terms_by_city[city] = term_count

    def search(self):
        for location in self.locations:
            offset = 0
            self.search_results = []
            while offset < self.page_limit and not self.repeated_results():
                r = requests.get(self.base_search_url%(location, offset))
                self.current_page = unicodedata.normalize('NFKD', r.text).encode('ascii','ignore')
                if r.status_code == 200:
                    self.search_results.append(self.current_page)
                    if location in self.job_map:
                        self.job_map[location].extend(self.get_joblinks_from_search())
                    else:
                        self.job_map[location] = self.get_joblinks_from_search()
                else:
                    print "Couldn't get: " + base_search_url%(location, offset)
                offset += 10
        self.get_job_data()

class Plot():

    def __init__(self, job_scraper):
        self.scraper = job_scraper
        self.data = {}
        self.prepare_data()

    def prepare_data(self):
        for city, term_count in self.scraper.terms_by_city.iteritems():
            skills_dict = {'R':term_count.get('r', 0), 'Python':term_count.get('python', 0),
                    'Java':term_count.get("java", 0), 'C++':term_count.get('c++', 0),
                    'Golang':term_count.get("go", 0), 'Rust':term_count.get('rust', 0),
                    'Ruby':term_count.get('ruby', 0),'Perl':term_count.get('perl', 0),
                    'JavaScript':term_count.get('javascript', 0), 'Scala':term_count.get('scala', 0),
                    'Excel':term_count.get('excel', 0), 'Tableau':term_count.get('tableau', 0),
                    'D3.js':term_count.get('d3.js', 0), 'SAS':term_count.get('sas', 0),
                    'SPSS':term_count.get('spss', 0), 'D3':term_count.get('d3.js', 0),
                    'Hadoop':term_count.get('hadoop', 0), 'MapReduce':term_count.get('mapreduce', 0),
                    'Spark':term_count.get('spark', 0), 'Pig':term_count.get('pig', 0),
                    'Hive':term_count.get('hive', 0), 'Shark':term_count.get('shark', 0),
                    'Oozie':term_count.get('oozie', 0), 'ZooKeeper':term_count.get('zookeeper', 0),
                    'Flume':term_count.get('flume', 0), 'Mahout':term_count.get('mahout', 0),
                    'SQL':term_count.get('sql', 0), 'NoSQL':term_count.get('nosql', 0),
                    'HBase':term_count.get('hbase', 0), 'Cassandra':term_count.get('cassandra', 0),
                    'MongoDB':term_count.get('mongodb', 0), 'Matlab':term_count.get('matlab', 0)}

            sorted_terms = sorted(skills_dict.items(), key=operator.itemgetter(1))
            sorted_terms = sorted_terms[-9:]

            terms = []
            counts = []
            
            for pair in sorted_terms:
                terms.append(pair[0])
                counts.append(pair[1])

            self.data[city] = [terms, counts]
            
    def plot(self):
        for city, data in self.data.iteritems():
            fig = plt.figure()
            ax = fig.add_subplot(111)

            ## necessary variables
            ind = np.arange(len(data[1]))
            width = 0.35                 

            rects1 = ax.bar(ind, data[1])
            
            # axes and labels
            ax.set_xlim(-width,len(ind)+width)
            ax.set_ylim(0,data[1][-1]+10)
            ax.set_ylabel('Mentions')
            ax.set_title('Most Requested Skills in ' + city)
            xTickMarks = data[0]
            ax.set_xticks(ind+width)
            xtickNames = ax.set_xticklabels(xTickMarks)
            plt.setp(xtickNames, rotation=45, fontsize=10)
        plt.show()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        a = JobScraper(sys.argv[1:])
        b = Plot(a)
        b.plot()
    else:
        print "No cities given"
        sys.exit()

