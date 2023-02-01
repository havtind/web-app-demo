from flask import Flask
from flask import request, render_template
import urllib.request
from flask import jsonify
import json
import random
import xml.etree.ElementTree as ET
from api_testing import pretty_print_xml
from urllib.request import urlopen
from datetime import datetime

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


def get_train_table():
    base_url_et = 'https://siri.opm.jbv.no/jbv/et/EstimatedTimetable.xml?'
    api_str = get_api_str(interval=10, line=None, direction=None, freighttrain=False)

    def get_api_xml_str(urlstr):
        try:
            with urlopen(base_url_et+urlstr) as response:
                body = response.read()
            return body.decode("utf-8")
        except ValueError:
            return 'Not able to make api call'

    print(base_url_et+api_str)
    xml_str = get_api_xml_str(api_str)
    root = ET.fromstring(xml_str)


    #folder='test_data/'
    #tree = ET.parse(folder+'et_0606_error.xml')
    #root = tree.getroot() 
    
    traindata = parse_xml_tree(root)
    return traindata


@app.route('/update', methods=['POST', 'GET'])
def update_func():
    #jsonString = json.dumps(list_of_train_dict2, indent=4)
    jsonString = json.dumps(get_train_table(), indent=4)
    return jsonString




def parse_xml_tree(root: ET.Element):
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
        train = {}
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
                    exp_departure = to_datetime(firstEstimatedCall.findtext(name_spc+'ExpectedDepartureTime'))
                    time_interval = get_time_difference(current_time, aim_departure)
                    last_stop = '-'
                    next_stop = firstEstimatedCall.findtext(name_spc+'StopPointName')
                    departure = '-'
                    arrival = aim_departure.strftime("%H:%M")
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
                    exp_arrival = to_datetime(firstEstimatedCall.findtext(name_spc+'ExpectedArrivalTime'))
                    time_interval = get_time_difference(current_time, aim_arrival)
                    last_stop = lastRecordedCall.findtext(name_spc+'StopPointName')
                    next_stop = firstEstimatedCall.findtext(name_spc+'StopPointName')
                    if not rec_departure:
                        departure = aim_departure.strftime("%H:%M")
                    else:
                        rec_departure = to_datetime(rec_departure)
                        departure = rec_departure.strftime("%H:%M")
                    arrival = aim_arrival.strftime("%H:%M")
                    delay = get_time_difference(aim_arrival, exp_arrival)
                else:
                    # Middle of journey.
                    status = firstEstimatedCall.findtext(name_spc+'DepartureStatus')
                    remark = ''
                    rec_departure = lastRecordedCall.findtext(name_spc+'ActualDepartureTime')
                    aim_arrival = to_datetime(firstEstimatedCall.findtext(name_spc+'AimedArrivalTime'))
                    exp_arrival = to_datetime(firstEstimatedCall.findtext(name_spc+'ExpectedArrivalTime'))
                    aim_departure = to_datetime(lastRecordedCall.findtext(name_spc+'AimedDepartureTime'))
                    time_interval = get_time_difference(current_time, aim_arrival)
                    last_stop = lastRecordedCall.findtext(name_spc+'StopPointName')
                    next_stop = firstEstimatedCall.findtext(name_spc+'StopPointName')
                    if not rec_departure:
                        departure = aim_departure.strftime("%H:%M")
                    else:
                        rec_departure = to_datetime(rec_departure)
                        departure = rec_departure.strftime("%H:%M")
                    arrival = aim_arrival.strftime("%H:%M")
                    delay = get_time_difference(aim_arrival, exp_arrival)
                if cancelled:
                    remark = 'Kansellert videre'
               
            if delay < 2:
                delay = ''
            else:
                delay_count += 1
                delay = f'+ {delay} min'
            
            if time_interval > 120:
                continue
            # For debugging
            #var = journey.findtext(name_spc+'DatedVehicleJourneyRef')
            #print(f'FEIL  {journey_count} {line} {origin} {destination} {var} ')
        
            single_journey = {
                'Nr':journey_count, 'Linje':line, 'Fra':origin, 'Til':destination, 
                'Med':operator, 'Forrige stasjon':last_stop, 'Utsjekket': departure, 'Neste stasjon':next_stop, 
                'Oppsatt': arrival, 'Forsinkelse': delay, 'Merknad':remark
                }
            journey_count += 1
            all_journeys.append(single_journey)
    all_journeys.append({'journeys':journey_count-1, 'delays':delay_count})
    return all_journeys

def to_datetime(time_str):
    return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S+01:00")


def get_time_difference(date1:datetime, date2:datetime):
    timedelta = max([date1, date2]) - min([date1, date2])
    seconds = timedelta.seconds
    minutes = seconds//60
    remainder = seconds%60
    if remainder > 20:
        minutes += 1
    return minutes



def get_time(timestamp: str):
    if timestamp:
        #2023-01-29T05:32:00+01:00
        timestamp = timestamp.removesuffix('+01:00')
        [date, time] = timestamp.split('T')
        [time, _] = time.rsplit(sep=':', maxsplit=1)
        return time
    else:
        return False

def get_time_difference2(time1:str, time2:str):
    # time1 < time2
    time1 = time1.split(':')
    time2 = time2.split(':')
    time1 = [int(i) for i in time1]
    time2 = [int(i) for i in time2]
    delay = 60*(time2[0]-time1[0]) + (time2[1]-time1[1])
    return delay



if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)
  







"""
@app.route("/1")
def converter():
    celsius = request.args.get("celsius", "")
    if celsius:
        fahrenheit = fahrenheit_from(celsius)
    else:
        fahrenheit = ""
    return (
        <form action="" method="get">
                <input type="text" name="celsius">
                <input type="submit" value="Convert">
              </form>
                + "Fahrenheit: "
                + fahrenheit
            )

@app.route("/2")
def get_kpi():
    url = "https://api.themoviedb.org/3/discover/movie?api_key={}"
    response = urllib.request.urlopen(url)
    data = response.read()
    dict = json.loads(data)
    return render_template ("movies.html", movies=dict["results"])

def fahrenheit_from(celsius):
    #Convert Celsius to Fahrenheit degrees.
    try:
        fahrenheit = float(celsius) * 9 / 5 + 32
        fahrenheit = round(fahrenheit, 3)  # Round to three decimal places
        return str(fahrenheit)
    except ValueError:
        return "invalid input"

"""