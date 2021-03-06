import PAsearchSites
import PAgenres
def tagAleadyExists(tag,metadata):
    for t in metadata.genres:
        if t.lower() == tag.lower():
            return True
    return False

def posterAlreadyExists(posterUrl,metadata):
    for p in metadata.posters.keys():
        Log(p.lower())
        if p.lower() == posterUrl.lower():
            Log("Found " + posterUrl + " in posters collection")
            return True

    for p in metadata.art.keys():
        if p.lower() == posterUrl.lower():
            return True
    return False

def search(results,encodedTitle,title,searchTitle,siteNum,lang,searchByDateActor,searchDate, searchAll, searchsiteID):
    searchResults = HTML.ElementFromURL('http://www.brazzers.com/search/all/?q=' + encodedTitle)
    for searchResult in searchResults.xpath('//h2[contains(@class,"scene-card-title")]//a'):
        Log(str(searchResult.get('href')))
        titleNoFormatting = searchResult.get('title')
        curID = searchResult.get('href').replace('/','_')
        lowerResultTitle = str(titleNoFormatting).lower()
        score = 100 - Util.LevenshteinDistance(title.lower(), titleNoFormatting.lower())
        
        results.Append(MetadataSearchResult(id = curID + "|" + str(siteNum), name = titleNoFormatting + " [Brazzers]", score = score, lang = lang))
    return results

def update(metadata,siteID,movieGenres):
    Log('******UPDATE CALLED*******')
    zzseries = False
    metadata.studio = 'Brazzers'
    temp = str(metadata.id).split("|")[0].replace('_','/')
    url = PAsearchSites.getSearchBaseURL(siteID) + temp
    detailsPageElements = HTML.ElementFromURL(url)

    # Summary
    paragraph = detailsPageElements.xpath('//p[@itemprop="description"]')[0].text_content()
    paragraph = paragraph.replace('&13;', '').strip(' \t\n\r"').replace('\n','').replace('  ','') + "\n\n"
    metadata.summary = paragraph[:-10]
    tagline = detailsPageElements.xpath('//span[@class="label-text"]')[0].text_content()
    metadata.collections.clear()
    metadata.tagline = tagline
    metadata.collections.add(tagline)
    metadata.title = detailsPageElements.xpath('//h1')[0].text_content()

    # Genres
    movieGenres.clearGenres()
    genres = detailsPageElements.xpath('//div[contains(@class,"tag-card-container")]//a')

    if len(genres) > 0:
        for genreLink in genres:
            genreName = genreLink.text_content().strip('\n').lower()
            movieGenres.addGenre(genreName)


    
    date = detailsPageElements.xpath('//aside[contains(@class,"scene-date")]')
    if len(date) > 0:
        date = date[0].text_content()
        date_object = datetime.strptime(date, '%B %d, %Y')
        metadata.originally_available_at = date_object
        metadata.year = metadata.originally_available_at.year
    

    # Starring/Collection 
    metadata.roles.clear()
    #starring = detailsPageElements.xpath('//p[contains(@class,"related-model")]//a')
    starring = detailsPageElements.xpath('//div[@class="model-card"]//a')
    memberSceneActorPhotos = detailsPageElements.xpath('//img[contains(@class,"lazy card-main-img")]')
    memberSceneActorPhotos_TotalNum = len(memberSceneActorPhotos)
    memberTotalNum = len(starring)/2
    Log('----- Number of Actors: ' +str(memberTotalNum) + ' ------')
    Log('----- Number of Photos: ' +str(memberSceneActorPhotos_TotalNum) + ' ------')
    
    memberNum = 0
    for memberCard in starring:
        # Check if member exists in the maleActors list as either a string or substring
        #if any(member.text_content().strip() in m for m in maleActors) == False:
            role = metadata.roles.new()
            # Add to actor and collection
            #role.name = "Test"
            memberName = memberCard.xpath('//h2[contains(@class,"model-card-title")]//a')[memberNum]
            memberPhoto = memberCard.xpath('//img[@class="lazy card-main-img" and @alt="'+memberName.text_content().strip()+'"]')[0].get('data-src')
            role.name = memberName.text_content().strip()
            memberNum = memberNum + 1
            memberNum = memberNum % memberTotalNum
            Log('--------- Photo   ---------- : ' + memberPhoto)
            role.photo = "http:" + memberPhoto.replace("model-medium.jpg","model-small.jpg")

    detailsPageElements.xpath('//h1')[0].text_content()

    #Posters
    i = 1
    try:
        background = "http:" + detailsPageElements.xpath('//*[@id="trailer-player"]/img')[0].get('src')
        Log("BG DL: " + background)
        metadata.art[background] = Proxy.Preview(HTTP.Request(background, headers={'Referer': 'http://www.google.com'}).content, sort_order = 1)
    except:
        pass
    for poster in detailsPageElements.xpath('//a[@rel="preview"]'):
        posterUrl = "http:" + poster.get('href').strip()
        thumbUrl = "http:" + detailsPageElements.xpath('//img[contains(@data-src,"thm")]')[i-1].get('data-src')
        if not posterAlreadyExists(posterUrl,metadata):            
            #Download image file for analysis
            try:
                img_file = urllib.urlopen(posterUrl)
                im = StringIO(img_file.read())
                resized_image = Image.open(im)
                width, height = resized_image.size
                #posterUrl = posterUrl[:-6] + "01.jpg"
                #Add the image proxy items to the collection
                if(width > 1):
                    # Item is a poster
                    
                    metadata.posters[posterUrl] = Proxy.Preview(HTTP.Request(posterUrl, headers={'Referer': 'http://www.google.com'}).content, sort_order = i)
                if(width > 100):
                    # Item is an art item
                    metadata.art[posterUrl] = Proxy.Preview(HTTP.Request(posterUrl, headers={'Referer': 'http://www.google.com'}).content, sort_order = i+1)
                i = i + 1
            except:
                pass


    return metadata