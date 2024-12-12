from flask import Flask
from flask import request, render_template
import urllib.request
from flask import jsonify
import json
import random
import xml.etree.ElementTree as ET

from urllib.request import urlopen
from datetime import datetime
from collections import defaultdict


app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html')



def get_api_str(interval:int, line:str=None, direction:str=None, freighttrain:bool=False):
    api_str = f'PreviewInterval=PT{interval}M'
    if line:
        api_str = api_str + f'&Lines.LineDirection.LineRef={line}'
    if direction:
        api_str = api_str + f'&Lines.LineDirection.DirectionRef={direction}'
    if not freighttrain:
        api_str = api_str + f'&ServiceFeatureRef=passengerTrain'
    return api_str



def get_train_table(interval, line, terminus, display):
    
    station_dict = {'Oslo S': 'OSL', 'Bergen': 'BRG', 'Eidsvoll': 'EVL', 'Kongsberg': 'KBG', 'Drammen': 'DRM', 'Lillehammer': 'LHM', 'Stavanger': 'STV', 'Egersund': 'EGS', 'Myrdal': 'MYR', 'Flåm': 'FM', 'Spikkestad': 'SPI', 'Lillestrøm': 'LLS', 'Trondheim S': 'TND', 'Bodø': 'BO', 'Göteborg C': 'GTB', 'Halden': 'HLD', 'Oslo Lufthavn': 'GAR', 'Moss': 'MOS', 'Nærbø': 'NBØ', 'Lundamo': 'LMO', 'Steinkjer': 'STK', 'Dombås': 'DOM', 'Åndalsnes': 'ÅND', 'Stabekk': 'STB', 'Ski': 'SKI', 'Kongsvinger': 'KVG', 'Asker': 'ASR', 'Hamar': 'HMR', 'Melhus': 'MSK', 'Mo i Rana': 'MO', 'Storlien': 'STR', 'Skien': 'SKN', 'Mysen': 'MYS', 'Arna': 'ARN', 'Mosjøen': 'MSJ', 'Gjøvik': 'GJØ', 'Røros': 'ROS', 'Dal': 'DAL', 'Jaren': 'JAR', 'Arendal': 'ADL', 'Nelaug': 'NEL'}

    if line=='':
        line = None
    if terminus=='':
        terminus = None
    elif terminus in station_dict.keys():
        terminus = station_dict[terminus]
    else:
        terminus = None
    base_url_et = 'https://siri.opm.jbv.no/jbv/et/EstimatedTimetable.xml?'
    api_str = get_api_str(interval=interval, line=line, direction=terminus, freighttrain=False)

    def get_api_xml_str(urlstr):
        try:
            with urlopen(urlstr) as response:
                """
                def get_kpi():
                url = "https://api.themoviedb.org/3/discover/movie?api_key={}"
                response = urllib.request.urlopen(url)
                data = response.read()
                dict = json.loads(data)
                return render_template ("movies.html", movies=dict["results"])
                """
                body = response.read()
            return body.decode("utf-8")
        except ValueError:
            return 'Not able to make api call'


    print(base_url_et+api_str)
    url_str = base_url_et+api_str

    xml_str = get_api_xml_str(url_str)
    root = ET.fromstring(xml_str)

    #folder='test_data/'
    #tree = ET.parse(folder+'et_40_norge_pass.xml')
    #root = tree.getroot() 
    
    traindata = parse_xml_tree(root, url_str, display='liten')
    return traindata


@app.route('/update', methods=['POST', 'GET'])
def update_func():
    # celsius = request.args.get("celsius", "")
    line = request.args.get('line')
    interval = request.args.get('interval')
    terminus = request.args.get('terminus')
    display = request.args.get('display')
    print(f'line: {line}   interval {interval}   terminus  {terminus}  ')
    jsonString = json.dumps(get_train_table(interval, line, terminus, display), indent=4)
    return jsonString




def parse_xml_tree(root: ET.Element, api_str:str, display:str):

    operator_dict = {'VY': 'VY', 'SJN': 'SJNord', 'GAG': 'GoAhead', 'VYG': 'VYGjøvikb.', 'FLY': 'Flytoget', 'VYT':'VY'}

    # tidspunkt hentet ut, 
    #'Nr', 'Linje', 'Fra', 'Til', 'Med', 'Forrige stasjon', 'Kl', 'Neste stasjon', 'Kl', 'Forsinkelse', 'Merknad']
    # ingen godstog
    # ingen tog som er ferdig med reisen.
    all_journeys = []
    name_spc = '{http://www.siri.org.uk/siri}'
    current_time = to_datetime(root[0].findtext(name_spc+'ResponseTimestamp'))

    journey_count = 1
    delay_count = 0
    journey_str = 'EstimatedVehicleJourney'

    for journey in root.iter(tag=name_spc+journey_str):
        """Iterates over all train journeys"""
        line = journey.findtext(name_spc+'LineRef')
        origin = journey.findtext(name_spc+'OriginName')
        destination = journey.findtext(name_spc+'DestinationName')
        operator = journey.findtext(name_spc+'OperatorRef')
        completed = False
        if not journey.find(name_spc+'EstimatedCalls'):
            completed = True  
        started = False
        if journey.find(name_spc+'RecordedCalls'):
            started = True
            
        if not completed:
            estimatedCalls = journey.find(name_spc+'EstimatedCalls')
            firstEstimatedCall = estimatedCalls[0]
            #firstEstimatedCall = estimatedCalls.find(name_spc+'EstimatedCall')
            cancelled = False
            if firstEstimatedCall.findtext(name_spc+'Cancellation')=='true':
                cancelled = True
            if firstEstimatedCall.findtext(name_spc+'DepartureStatus')=='cancelled': 
                cancelled = True

            if not started:
                if cancelled:
                    # Maybe use ['firstEstimatedCall.findtext(name_spc+'DepartureStatus')=='cancelled']
                    status = firstEstimatedCall.findtext(name_spc+'DepartureStatus')
                    remark = 'Kansellert'
                    aim_departure = to_datetime(firstEstimatedCall.findtext(name_spc+'AimedDepartureTime'))
                    time_interval = get_time_difference(current_time, aim_departure)
                    last_stop = '-'
                    next_stop = firstEstimatedCall.findtext(name_spc+'StopPointName')
                    departure = '-'
                    arrival = aim_departure.strftime("%H:%M")
                    delay = 0
                else:
                    # Journey will start soon.
                    status = firstEstimatedCall.findtext(name_spc+'DepartureStatus')
                    remark = 'Ikke startet'
                    aim_departure = to_datetime(firstEstimatedCall.findtext(name_spc+'AimedDepartureTime'))
                    exp_departure = firstEstimatedCall.findtext(name_spc+'ExpectedDepartureTime')
                    time_interval = get_time_difference(current_time, aim_departure)
                    last_stop = '-'
                    next_stop = firstEstimatedCall.findtext(name_spc+'StopPointName')
                    departure = '-'
                    
                    if not exp_departure:
                        arrival = aim_departure.strftime("%H:%M")
                        delay = 0
                    else:
                        exp_departure = to_datetime(exp_departure)
                        arrival = exp_departure.strftime("%H:%M")
                        delay = get_time_difference(aim_departure, exp_departure)
            else:
                recordedCalls = journey.find(name_spc+'RecordedCalls')
                lastRecordedCall = recordedCalls[-1]
                if not firstEstimatedCall.findtext(name_spc+'DepartureStatus'):
                    # Next station is terminus.
                    status = firstEstimatedCall.findtext(name_spc+'ArrivalStatus')
                    remark = 'Terminus neste'
                    rec_departure = lastRecordedCall.findtext(name_spc+'ActualDepartureTime')
                    aim_departure = to_datetime(lastRecordedCall.findtext(name_spc+'AimedDepartureTime'))
                    aim_arrival = to_datetime(firstEstimatedCall.findtext(name_spc+'AimedArrivalTime'))
                    exp_arrival = firstEstimatedCall.findtext(name_spc+'ExpectedArrivalTime')
                    time_interval = get_time_difference(current_time, aim_arrival)
                    last_stop = lastRecordedCall.findtext(name_spc+'StopPointName')
                    next_stop = firstEstimatedCall.findtext(name_spc+'StopPointName')
                    if not rec_departure:
                        departure = 'ingen info'
                    else:
                        rec_departure = to_datetime(rec_departure)
                        departure = rec_departure.strftime("%H:%M")
                    if not exp_arrival:
                        arrival = 'ingen info'
                        delay = 0
                    else:
                        exp_arrival = to_datetime(exp_arrival)
                        arrival = exp_arrival.strftime("%H:%M")
                        delay = get_time_difference(aim_arrival, exp_arrival)
                else:
                    # Middle of journey.
                    status = firstEstimatedCall.findtext(name_spc+'DepartureStatus')
                    remark = ''
                    rec_departure = lastRecordedCall.findtext(name_spc+'ActualDepartureTime')
                    aim_arrival = to_datetime(firstEstimatedCall.findtext(name_spc+'AimedArrivalTime'))
                    exp_arrival = firstEstimatedCall.findtext(name_spc+'ExpectedArrivalTime')
                    aim_departure = to_datetime(lastRecordedCall.findtext(name_spc+'AimedDepartureTime'))
                    time_interval = get_time_difference(current_time, aim_arrival)
                    last_stop = lastRecordedCall.findtext(name_spc+'StopPointName')
                    next_stop = firstEstimatedCall.findtext(name_spc+'StopPointName')
                    if not rec_departure:
                        departure = 'ingen info'
                    else:
                        rec_departure = to_datetime(rec_departure)
                        departure = rec_departure.strftime("%H:%M")
                    if not exp_arrival:
                        arrival = 'ingen info'
                        delay = 0
                    else:
                        exp_arrival = to_datetime(exp_arrival)
                        arrival = exp_arrival.strftime("%H:%M")
                        delay = get_time_difference(aim_arrival, exp_arrival)

                if cancelled:
                    if display=='liten':
                        remark = 'Delvis kansellert'
                    else:
                        remark = 'Kansellert videre'
                
            if delay < 2:
                delay = ''
            else:
                delay_count += 1
                delay = f'{delay} min'
            
            if time_interval > 120:
                continue

            if operator not in operator_dict.keys():
                operator='Ukjent'
            else:
                operator=operator_dict[operator]
            single_journey = {
                'Linje':line, 'Fra':origin, 'Til':destination, 
                'Operatør': operator, 'Neste stasjon':next_stop, 'Estimert': arrival, 'Avvik': delay, 'Merknad':remark
                }      
            journey_count += 1
            all_journeys.append(single_journey)
    if journey_count == 1:
        single_journey = {
                'Linje': '-', 'Fra':'-', 'Til':'-', 
                'Operatør': '-', 'Neste stasjon':'-', 'Estimert': '-', 'Avvik': '-', 'Merknad':'Ingen oppsatte tog!'
                }   
        all_journeys.append(single_journey)
    all_journeys.append({'journeys':journey_count-1, 'delays': delay_count, 'api_str': api_str})
    return all_journeys

def to_datetime(time_str):
    try:
        return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S+01:00")
    except:
        # summer time
        return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S+02:00")

def get_time_difference(date1:datetime, date2:datetime):
    timedelta = max([date1, date2]) - min([date1, date2])
    seconds = timedelta.seconds
    minutes = seconds//60
    remainder = seconds%60
    if remainder > 20:
        minutes += 1
    return minutes


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)