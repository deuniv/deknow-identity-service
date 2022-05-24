import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlunparse

URL_TYPE_ARTICLE = 0
URL_TYPE_UNKNOWN = -1
URL_TYPE_PROFILE = 1

def getPubIdFromCitationsUrl(url=""):
    parsedUrl = urlparse(url)
    parsedQuery = parse_qs(parsedUrl.query)
    if 'cites' in parsedQuery:
        pubId = parsedQuery['cites'][0]
        if "," in pubId:
            # Sometimes there are multiple publication IDs to a publication 
            # Could be for different languages eg: https://scholar.google.com/citations?view_op=view_citation&hl=en&user=hkhcWG4AAAAJ&citation_for_view=hkhcWG4AAAAJ:u5HHmVD_uO8C)
            return pubId.split(",")[0].strip()
        return pubId

def convertToLanguage(url, lang="en"):
    # hl is a parameter that is passed to set the language of the returned page.
    # We can change it to work in a different langugage
    parsedUrl = urlparse(url)
    parsedQuery = parse_qs(parsedUrl.query)
    if 'hl' in parsedQuery:
        newQuery = parsedUrl.query.replace("hl="+parsedQuery['hl'][0], "hl=en")
    else:
        parsedQuery['hl'] = [lang]
    parsedUrl = parsedUrl._replace(query=newQuery)
    return urlunparse(parsedUrl)

def parseUrlAndFetch(db, url):
    if url == None or url == "":
        return returnError("URL_REQUIRED")
    url = url.strip()
    urlType = getUrlType(url)
    # Setting the URLs to return English pages.
    if urlType == URL_TYPE_ARTICLE:
        url = convertToLanguage(url)
        return fetchArticleDetails(db, url)
    elif urlType == URL_TYPE_PROFILE:
        url = convertToLanguage(url)
        return fetchProfileDetails(db, url)
    else:
        return returnError("URL_NOT_SUPPORTED")
    
def returnError(msg=""):
    return {"success": False, "error": msg}

def fetchArticleDetails(db, url=""):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        return returnError(e)

    result = {}
    result["url_requested"] = url
    result["url_type"] = "Article"
    
    # Parse the title related details
    titleSection = soup.find(class_="gsc_oci_title_link")
    if titleSection:
        result["title"] = titleSection.text
        result["link"] = titleSection["href"]
    
    # Parse the publication details as provided
    details = {}
    detailsSection = soup.find_all(class_="gs_scl")
    for detailSection in detailsSection:
        field = detailSection.find(class_="gsc_oci_field")
        value = detailSection.find(class_="gsc_oci_value")
        if field and value:
            if field.text == "Total citations":
                value = value.find("a")
                if value:
                    refUrl = value['href']
                    parsedUrl = urlparse(refUrl)
                    parsedQuery = parse_qs(parsedUrl.query)
                    if 'cites' in parsedQuery:
                        value = parsedQuery['cites'][0]
                        details["Publication ID"] = value
            else:
                details[field.text] = value.text.strip()

    # Format standardization of the result
    for d in details:
        if d in ["Authors", "Publication date", "Description", "Publication ID"]:
            result[d.lower().replace(" ","_")] = details[d]
        elif d in ["Source", "Volume", "Issue", "Pages", "Publisher"]:
            if details[d] != "":
                result["source"] = (result.get("source", "") + ", {}: {}".format(d, details[d]))
    result["source"] = result["source"][2:].strip()

    # Check if db already has the data -> update or create
    try:
        t = db.execute(
            "INSERT INTO publication (gsc_pub_id, title, link, authors, publication_date, source, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ((result['publication_id']), result['title'], result['link'], result['authors'], result['publication_date'], result['source'], result['description']),
        )
        t = db.commit()
    except db.IntegrityError as e:
        t = db.execute(
            "UPDATE publication SET title = ?, link = ?, authors = ?, publication_date = ?, source = ?, description = ? WHERE id = ?",
            (result['title'], result['link'], result['authors'], result['publication_date'], result['source'], result['description'], result['publication_id']),
        )
        t = db.commit()
    except Exception as e:
        print("Error - {}".format(e))
    return result

def fetchProfileDetails(db, url="", pubLimit=5):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        return returnError(e)

    result = {}
    result["url_requested"] = url
    result["url_type"] = "Profile"
    result["publications"] = []

    # Parse the profile related details
    profileSection = soup.find(id="gsc_prf")
    if profileSection:
        profileImg = profileSection.find(id="gsc_prf_pup-img")
        if profileImg:
            result["profile_img"] = profileImg["src"]
        profileName = profileSection.find(id="gsc_prf_in")
        if profileName:
            result["author"] = profileName.text

    # Parse the publications
    publications = soup.find_all(class_="gsc_a_tr")
    if not publications:
        return result
    # Publications limited to top [pubLimit] number of publications.
    for publication in publications[0:pubLimit]:
        pub = {}
        # Fetching the title and link of the publication
        titleDetailsSection = publication.find(class_="gsc_a_t")
        if titleDetailsSection:
            title = titleDetailsSection.find('a')
            pub["title"] = title.text
            pub["link"] = "https://scholar.google.com/{}".format(title["href"])
            details = titleDetailsSection.find_all(class_='gs_gray')
            if len(details) >= 2:
                pub["authors"] = details[0].text
                pub["source"] = details[1].text
        # Fetching the cited by details to get the id of the publication
        citedBySection = publication.find(class_="gsc_a_c")
        if citedBySection:
            citationsLink = citedBySection.find('a')
            if citationsLink:
                refUrl = citationsLink['href']
                pub["publication_id"] = getPubIdFromCitationsUrl(refUrl)
        # Fetching the year details       
        yearSection = publication.find(class_="gsc_a_y")
        if yearSection:
            pub["publication_date"] = yearSection.text
        result["publications"].append(pub)

    # TODO: Store in DB
    return result

def isProfileUrl(url=""):
    # Checks if this URL can be parsed by looking at the url params.
    # Eg: https://scholar.google.com/citations?view_op=list_works&hl=en&hl=en&user=DLBorCEAAAAJ
    # User is important and if view_op is present it must be "list_works"
    parsedUrl = urlparse(url)
    if parsedUrl.netloc != "scholar.google.com":
        return False
    if parsedUrl.path != "/citations":
        return False
    parsedQuery = parse_qs(parsedUrl.query)
    if 'user' in parsedQuery:
        if 'view_op' in parsedQuery:
            if parsedQuery['view_op'][0] == "list_works":
                return True
            else:
                return False
        return True
    return False

def isArticleUrl(url=""):
    # Checks if this URL can be parsed by looking at the url params.
    # https://scholar.google.com/citations?view_op=view_citation&hl=en&user=DLBorCEAAAAJ&citation_for_view=DLBorCEAAAAJ:HDshCWvjkbEC
    parsedUrl = urlparse(url)
    if parsedUrl.netloc != "scholar.google.com":
        return False
    if parsedUrl.path != "/citations":
        return False
    parsedQuery = parse_qs(parsedUrl.query)
    if 'view_op' in parsedQuery and 'citation_for_view' in parsedQuery and parsedQuery['view_op'][0] == "view_citation":
        return True
    return False

def getUrlType(url=""):
    if isProfileUrl(url):
        return URL_TYPE_PROFILE
    elif isArticleUrl(url):
        return URL_TYPE_ARTICLE
    else:
        return URL_TYPE_UNKNOWN