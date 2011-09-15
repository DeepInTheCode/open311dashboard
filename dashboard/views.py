try:
    import simplejson as json
except:
    import json

from datetime import datetime
import re
import urllib
import urllib2

from django.template import Context
from django.shortcuts import render # , redirect
from django.http import HttpResponse

from pymongo.connection import Connection
import bson.json_util

from settings import MONGODB

# Set up the database connection as a global variable
connection = Connection(MONGODB['host'])
db = connection[MONGODB['db']]

def index(request, geography=None, is_json=False):
    """
    Homepage view. Can also return json for the city or neighborhoods.
    """
    c = Context({'test' : "Hello World!"})
    return render(request, 'index.html', c)

# Neighborhood specific pages.
def neighborhood_list(request):
    """
    List the neighborhoods.
    """
    # neighborhoods = Geography.objects.all()
    neighborhoods = db.polygons.find({ 'properties.type' : 'neighborhood' })

    c = Context({
        'neighborhoods': neighborhoods
        })

    return render(request, 'neighborhood_list.html', c)


def neighborhood_detail(request, neighborhood_slug):
    """

    Show detail for a specific neighborhood. Uses templates/geo_detail.html

    """
    neighborhood = db.polygons \
            .find_one({ 'properties.slug' : neighborhood_slug})
    requests = db.requests.find({'coordinates' :
        { '$within' : neighborhood['geometry']['coordinates'] }
        }).limit(10)

    c = Context({
        'neighborhood' : neighborhood,
        'requests' : requests
        })

    return render(request, 'neighborhood_test.html', c)

# Street specific pages.
def street_list(request):
    """

    List the top 10 streets by open service requests.

    """
    streets = db.streets.find({}).limit(25)
    c = Context({
        'streets' : streets
        })

    return render(request, 'street_list.html', c)

def street_specific_list(request, street_name):
    """
    View all of the blocks on a street.
    """
    streets = db.streets.find({ 'properties.slug' : street_name})

    c = Context({ 'streets' : streets })
    return render(request, 'street_list.html', c)


def street_view(request, street_name, min_val, max_val):
    """
    View details for a specific street. Renders geo_detail.html like
    neighborhood_detail does.
    """
    street = db.streets.find_one( {
        'properties.slug' : street_name,
        'properties.min' : int(min_val),
        'properties.max' : int(max_val) }
        )

    c = Context({
        'street': street,
        'json' : json.dumps(street['geometry'])
        })

    return render(request, 'street_test.html', c)

def api_handler(request, collection):
    """
    Serialize values returned from the database.
    """
    resp = []
    lookup = {}
    get_params = request.GET.copy()
    geo_collections = ['polygons', 'streets']

    if collection in geo_collections:
        prefix = 'properties.'
    else:
        prefix = ''

    # What page number?
    if 'page' in get_params:
        page = int(get_params.get('page'))
        del get_params['page']
    else:
        page = 1

    # How big should the page be?
    if 'page_size' in get_params:
        page_size = int(get_params['page_size'])
        del get_params['page_size']
    else:
        page_size = 1000

    # Handle the special methods
    for k, v in get_params.iteritems():

        # Handle dates.
        if re.search('date', k):
            year, month, day = v.split('-')
            v = datetime(int(year), int(month), int(day))

        # Ranges
        r = re.search('^(?P<key>.+)_(?P<side>start|end)$', k)
        if r:
            matches = r.groupdict()
            k = matches['key']
            map_dict = { 'start' : "$gte", 'end' : '$lte' }

            if k in lookup:
                lookup_v = lookup[k]
            else:
                lookup_v = {}

            lookup_v[map_dict[matches['side']]] = v
            v = lookup_v

        # Inside polygon.
        bounds = re.search('^(?P<key>.+)_bounds$', k)
        if bounds:
            if collection in geo_collections:
                prefix = 'geometry.'

            key = bounds.groups()[0]
            json_bounds = json.loads(v)
            lookup_type = '$box' if len(json_bounds) == 2 else '$polygon'

            k = key
            v = {'$within' : { lookup_type : json_bounds }}

        lookup['%s%s' % (prefix, k)] = v

    try:
        results = db[collection].find(lookup,
                skip=(page_size * (page-1)), limit=page_size)
    except:
        return HttpResponse('Error',status=400)

    for row in results:
        del row['_id']
        resp.append(row)

        # TODO: Clean up datetimes.

    if collection in geo_collections:
        resp = { 'type' : "FeatureCollection",
                'features' : resp }

    json_resp = json.dumps(resp, default=bson.json_util.default)
    return HttpResponse(json_resp, 'application/json')


# Search for an address!
def street_search(request):
    """
    Do a San Francisco specific geocode and then match that against our street
    centerline data.
    """
    query = request.GET.get('q')
    lat = request.GET.get('lat')
    lon = request.GET.get('lng')
    if not query:
        # They haven't searched for anything.
        return render(request, 'search.html')
    elif query and not lat:
        # Lookup the search string with Yahoo!
        url = "http://where.yahooapis.com/geocode"
        params = {"addr": query,
                "line2": "San Francisco, CA",
                "flags": "J",
                "appid": "1I9Jh.3V34HMiBXzxZRYmx.DO1JfVJtKh7uvDTJ4R0dRXnMnswRHXbai1NFdTzvC" }

        query_params = urllib.urlencode(params)
        data = urllib2.urlopen("%s?%s" % (url, query_params)).read()

        temp_json = json.loads(data)

        if temp_json['ResultSet']['Results'][0]['quality'] > 50:
            lon = temp_json['ResultSet']['Results'][0]["longitude"]
            lat = temp_json['ResultSet']['Results'][0]["latitude"]
        else:
            lat, lon = None, None

    """ if lat and lon:
        nearest_street = Street.objects \
                               .filter(line__dwithin=(point, D(m=100))) \
                               .distance(point).order_by('distance')[:1]
        try:
            return redirect(nearest_street[0])
        except IndexError:
            pass
    c = Context({'error': True})
    return render(request, 'search.html', c) """


def map(request):
    """
    Simply render the map.

    TODO: Get the centroid and bounding box of the city and set that. (See
    neighborhood_detail and geo_detail.html for how this would look)
    """
    return render(request, 'map.html')
