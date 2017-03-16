import scrapy, time, cookielib, os, json, urllib2
from lxml import html
from scrapy.http import Request
import requests
from fake_useragent import UserAgent
from random import randint

from ..items import AngelListItem
try:
     os.remove('parser_list.cookies.txt')
except:
    pass
try:
     os.remove('parser_detail.cookies.txt')
except:
    pass

try:
     os.remove('parser_personal.cookies.txt')
except:
    pass

class AngelInParser():
    def __init__(self, flag=''):
        """ Start up... """
        self.ua = UserAgent()
        if flag == 1:
            cookie_filename = "parser_list.cookies.txt"
        elif flag==2:
            cookie_filename = "parser_detail.cookies.txt"
        else:
            cookie_filename = "parser_personal.cookies.txt"

        # Simulate browser with cookies enabled

        self.cj = cookielib.MozillaCookieJar(cookie_filename)
        if os.access(cookie_filename, os.F_OK):
            self.cj.load()
        self.opener = urllib2.build_opener(
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler(debuglevel=0),
            urllib2.HTTPSHandler(debuglevel=0),
            urllib2.HTTPCookieProcessor(self.cj)
        )
        # if flag == 1:
        #     self.opener.addheaders = [
        #         ('User-agent', ('Mozilla/4.0 (compatible; MSIE 6.0; '
        #                         'Windows NT 5.2; .NET CLR 1.1.4322)'))
        #     ]
        # else:
        self.opener.addheaders = [
                ('User-agent', (str(self.ua.random)))
            ]

        # Login
        # self.loginPage(self.url,flag)



        self.cj.save()


    def loadPage(self, url):
        """
        Utility function to load HTML from URLs for us with hack to continue despite 404
        """
        # We'll print the url in case of infinite loop
        # print "Loading URL: %s" % url
        try:

            response = self.opener.open(url)

            return ''.join(response.readlines())
        except:
            # If URL doesn't load for ANY reason, try again...
            # Quick and dirty solution for 404 returns because of network problems
            # However, this could infinite loop if there's an actual problem
            pass

    def loginPage(self, url, flag):
        """
        Handle login. This should populate our cookie jar.
        """
        html = self.loadPage(url)
        if flag != 1:
            return html
            # print "DATA:",html


class AngelSpider(scrapy.Spider):
    name = "angel"

    start_urls = ['https://angel.co/companies']

    def __init__(self):

        self.start()

    def start(self, ):
        yield scrapy.http.Request(url=self.start_urls[0], callback=self.parse)

    def parse(self, response):
        time.sleep(randint(0,60))
        parser = AngelInParser(1)
        data = parser.loginPage("https://angel.co/companies", 1)
        print "LOAD COOKIE:"
        final_data = []
        cj = cookielib.MozillaCookieJar('parser_list.cookies.txt')
        cj.load()
        header = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        }
        angel_list = requests.Session()
        angel_list.cookies = cj
        count = 1
        while True:
            try:
                d = {"sort": "signal", "page": count}
                r = angel_list.post(url='https://angel.co/company_filters/search_data', data=json.dumps(d),
                                    headers=header)
                time.sleep(randint(0,240))
                post_data = json.loads(r.text)
                id_data = post_data["ids"]
                total_data = post_data["total"]
                page_data = post_data["page"]
                sort_data = post_data["sort"]
                new_data = post_data["new"]
                hexdigest_data = post_data["hexdigest"]

                get_url = "https://angel.co/companies/startups?"
                for entry in id_data:
                    get_url = get_url + "ids[]=" + str(entry) + "&"

                get_url = get_url + "total=" + str(total_data) + "&page=" + str(page_data) + "&sort=" + str(
                    sort_data) + "&new=" + str(new_data) + "&hexdigest=" + str(hexdigest_data)
                print"COUNT:", count

                list_data = angel_list.get(url=get_url)
                # print "DATA:",str(list_data.text)
                time.sleep(randint(0,240))
                try:
                 temp_data = json.loads(list_data.text)
                except:
                  print"CANNOT LOAD JSON"
                  pass

                doc = html.fromstring(temp_data["html"])

                href_list = doc.xpath("//div[contains(@class, 'name')]/a/@href")

                name_list = doc.xpath("//div[contains(@class, 'name')]/a/text()")

                des_list = doc.xpath("//div[contains(@class, 'pitch')]/text()")

                stage_list = doc.xpath(
                    "//div[contains(@class, 'column hidden_column stage')]/div[contains(@class,'value')]/text()")

                for i in range(0, len(name_list)):
                    print"NEXT"
                    item = AngelListItem()
                    company_detail_data = self.parse_company_details(href_list[i])
                    print"<<<<<<<COMPANY>>>>>>>>>>"
                    try:
                     name=name_list[i]
                    except:
                     name=None
                    try:
                     href=href_list[i]
                    except:
                     href=None
                    try:
                     detail=company_detail_data[4] + des_list[i].replace("\n", "")
                    except:
                     detail=None
                    try:
                     stage=stage_list[i].replace("\n", "")
                    except:
                     stage=None
                    try:
                     location=company_detail_data[0]
                    except:
                     location=None
                    try:
                     market=company_detail_data[1]
                    except:
                     market=None
                    try:
                     founder=company_detail_data[2]
                    except:
                     founder=None
                    try:
                     emp_no=company_detail_data[3]
                    except:
                     emp_no=None


                    # print detail_des

                    # final_data.append({"name": name_list[i], "angel_url": href_list[i],
                    #                    "description": company_detail_data[4] + des_list[i].replace("\n", ""),
                    #                    "stage": stage_list[i].replace("\n", ""), "location": company_detail_data[0],
                    #                    "market": company_detail_data[1],
                    #                    "founder": company_detail_data[2], "employe_num": company_detail_data[2]})
                    item["name"] = name
                    item["description"] = detail
                    item["employe_num"] = emp_no
                    item["stage"] = stage
                    item["location"] = location
                    item["market"] =market
                    item["founder"] = founder

                    yield item
                count = count + 1

            except:
                print"LOOP COMPLETED"
                break

    def parse_company_details(self, url):
        time.sleep(randint(0,60))
        detail_company = AngelInParser(2)
        detail_data = detail_company.loginPage(url, 2)
        time.sleep(randint(0,240))
        detail_doc = html.fromstring(detail_data)
        try:
            location = detail_doc.xpath("//span[contains(@class,'js-location_tags')]/a/text()")[0]
        except:
            location = None

        try:
            market = detail_doc.xpath("//span[contains(@class,'js-market_tags')]/a/text()")
        except:
            market = None
        try:
            founder = detail_doc.xpath(
                "//div[contains(@class,'g-lockup larger top')]/div[contains(@class,'text')]/div[contains("
                "@class,'name')]/a[contains(@class,'profile-link')]/@href")
            founder_data=[]
            for entry in founder:
                return_data=self.parse_personal_details(entry)
                founder_data.append({"angel_url":entry,"linkdin":return_data[0],"designation":return_data[1]})
            founder=founder_data
        except:
            founder = None
        try:
            employ_num = detail_doc.xpath("//span[contains(@class,'js-company_size')]/text()")[0].replace(
                "\n", "")
        except:
            employ_num = None
        try:
            detail_desc = detail_doc.xpath("//div[contains(@class,'content')]/text()")
            detail_desc = max(detail_desc, key=len)
            detail_desc = detail_desc.replace("\n", "")
        except:
            detail_desc = None
        return [location, market, founder, employ_num, detail_desc]

    def parse_personal_details(self,url):
        print"IN"

        try:
         detail_personal = AngelInParser(3)
        except:
         print"1"
        try:
         detail_personal_data =detail_personal.loginPage(url,3)
         time.delay(randint(0,240))
        except:
         print "2"
        try:
         detail_personal_doc = html.fromstring(detail_personal_data)
        except:
         print"3"
        try:
         linked_in=detail_personal_doc.xpath("//a[contains(@class,'icon link_el fontello-linkedin')]/@href")
        except:
         linked_in=None
        try:
         designation=detail_personal_doc.xpath("//div[contains(@class,'dm77 fud43 _a _jm')]/p/text()")
        except:
         designation=None
        # print designation
        # print linked_in
        return [linked_in,designation]
