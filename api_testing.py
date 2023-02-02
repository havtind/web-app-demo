
from urllib.request import urlopen
import xml.etree.ElementTree as ET


base_url_et = 'https://siri.opm.jbv.no/jbv/et/EstimatedTimetable.xml?'


name_spc = '{http://www.siri.org.uk/siri}'




def get_api_xml_str(urlstr):
    try:
        with urlopen(base_url_et+urlstr) as response:
            body = response.read()
        return body.decode("utf-8")
    except ValueError:
        return 'Not able to make api call'


def get_saved_xml_str(file_name):
    with open(file_name+'.txt') as f:
        lines = f.readlines()
    return lines[0]


def get_time_date(timestamp: str):
    #2023-01-29T05:32:00+01:00
    if timestamp:
        timestamp = timestamp.removesuffix('+01:00')
        [date, time] = timestamp.split('T')
        [time, _] = time.rsplit(sep=':', maxsplit=1)
        return time, date
    else:
        return 'XX'

station_dict = {'Oslo S': 'OSL', 'Bergen': 'BRG', 'Eidsvoll': 'EVL', 'Kongsberg': 'KBG', 'Drammen': 'DRM', 'Lillehammer': 'LHM', 'Stavanger': 'STV', 'Egersund': 'EGS', 'Myrdal': 'MYR', 'Flåm': 'FM', 'Spikkestad': 'SPI', 'Lillestrøm': 'LLS', 'Trondheim S': 'TND', 'Bodø': 'BO', 'Göteborg C': 'GTB', 'Halden': 'HLD', 'Oslo Lufthavn': 'GAR', 'Moss': 'MOS', 'Nærbø': 'NBØ', 'Lundamo': 'LMO', 'Steinkjer': 'STK', 'Dombås': 'DOM', 'Åndalsnes': 'ÅND', 'Stabekk': 'STB', 'Ski': 'SKI', 'Kongsvinger': 'KVG', 'Asker': 'ASR', 'Hamar': 'HMR', 'Melhus': 'MSK', 'Mo i Rana': 'MO', 'Storlien': 'STR', 'Skien': 'SKN', 'Mysen': 'MYS', 'Arna': 'ARN', 'Mosjøen': 'MSJ', 'Gjøvik': 'GJØ', 'Røros': 'ROS', 'Dal': 'DAL', 'Jaren': 'JAR', 'Arendal': 'ADL', 'Nelaug': 'NEL'}

def pretty_print_xml(root: ET.Element):
    journey = 'EstimatedVehicleJourney'
    count = 1
    station_dict = {}
    for tex in root.iter(tag=name_spc+journey):
        lineref = tex.findtext(name_spc+'LineRef')
        destination = tex.findtext(name_spc+'DestinationName')
        origin = tex.findtext(name_spc+'OriginName')
        operator = tex.findtext(name_spc+'OperatorRef')

        station_dict[destination] = tex.findtext(name_spc+'DirectionRef')
        station_dict[origin] = tex.findtext(name_spc+'OriginRef')        

        """
        started = False
        done = False
        if tex.find(name_spc+'RecordedCalls'):
            started = True
        if not tex.find(name_spc+'EstimatedCalls'):
            done = True
        
        if not done:
            estimatedCalls = tex.find(name_spc+'EstimatedCalls')
            firstEstimatedCall = estimatedCalls.find(name_spc+'EstimatedCall')
            avgang_stamp = firstEstimatedCall.findtext(name_spc+'AimedDepartureTime')
            avgang, _ = get_time_date(avgang_stamp) 
            status = firstEstimatedCall.findtext(name_spc+'DepartureStatus')
            next_stop = firstEstimatedCall.findtext(name_spc+'StopPointName')

            
            merknad = ''
            if not status:
                status = firstEstimatedCall.findtext(name_spc+'ArrivalStatus')
                avgang_stamp = firstEstimatedCall.findtext(name_spc+'AimedArrivalTime')
                avgang, _ = get_time_date(avgang_stamp)
                merknad = 'siste stopp'
            if not started:
                merknad = 'ikke startet'
            if lineref=='-':
                merknad = 'godstog'

            print(f'{count:3} Linje {lineref:7} fra {origin:17} til {destination:17}  med {operator:5}  neste {next_stop:17} kl {avgang:7}', end='')

            delay=0
            if status=='delayed':
                expected_stamp = firstEstimatedCall.findtext(name_spc+'ExpectedDepartureTime')
                if not expected_stamp:
                    expected_stamp = firstEstimatedCall.findtext(name_spc+'ExpectedArrivalTime')
                expected, _ = get_time_date(expected_stamp)

                if not lineref=='-':
                    delay = get_time_difference(avgang, expected)
                    print(f'+{delay:3}m  ', end='')
                else:
                    print(f'{" ":7}', end='')

            elif status=='cancelled':
                print(f'cnclld ', end='')
                pass
            else:
                print(f'{" ":7}', end='')
                pass

            print(f' {merknad:14} ')
        else:
            print(f'{count:3} Linje {lineref:7} fra {origin:17} til {destination:17}  med {operator:5}  neste {"-":17} kl {"-":7}', end='')
            print(f'{" ":7}', end='')
            print(f'{" ":7}', end='')
            merknad = 'ferdig'
            print(f' {merknad:14} ')
        """
        count += 1
    """
    set_lines = set(lines)
    list_res = (list(set_lines))
    list_res = sorted(list_res)
    print(list_res)
    """
    print(station_dict)

def get_api_str(interval:int, line:str=None, direction:str=None, freighttrain:bool=False):
    api_str = f'PreviewInterval=PT{interval}M'
    if line:
        api_str = api_str + f'&Lines.LineDirection.LineRef={line}'
    if direction:
        api_str = api_str + f'&Lines.LineDirection.DirectionRef={direction}'
    if not freighttrain:
        api_str = api_str + f'&ServiceFeatureRef=passengerTrain'
    return api_str






def parse_xml_tree(root: ET.Element):
    # tidspunkt hentet ut, 
    #'Nr', 'Linje', 'Fra', 'Til', 'Med', 'Forrige stasjon', 'Kl', 'Neste stasjon', 'Kl', 'Forsinkelse', 'Merknad']
    # ingen godstog
    # ingen tog som er ferdig med reisen.
    all_journeys = []

    name_spc = '{http://www.siri.org.uk/siri}'
    data_timestamp = None
    journey_count = 1
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
            # vurder firstEstimatedCall = estimatedCalls[0]
            firstEstimatedCall = estimatedCalls.find(name_spc+'EstimatedCall')
            cancelled = False
            if firstEstimatedCall.findtext(name_spc+'Cancellation')=='true':
                cancelled = True

            if not started:
                if cancelled:
                    # Maybe use ['firstEstimatedCall.findtext(name_spc+'DepartureStatus')=='cancelled']
                    status = firstEstimatedCall.findtext(name_spc+'DepartureStatus')
                    remark = 'Kansellert'
                    aim_departure = get_time(firstEstimatedCall.findtext(name_spc+'AimedDepartureTime'))
                    last_stop = firstEstimatedCall.findtext(name_spc+'StopPointName')
                    next_stop = '-'
                    departure = aim_departure
                    arrival = '-'
                    delay = ''
                else:
                    # Journey will start soon.
                    status = firstEstimatedCall.findtext(name_spc+'DepartureStatus')
                    remark = 'Ikke startet'
                    aim_departure = get_time(firstEstimatedCall.findtext(name_spc+'AimedDepartureTime'))
                    exp_departure = get_time(firstEstimatedCall.findtext(name_spc+'ExpectedDepartureTime'))
                    last_stop = firstEstimatedCall.findtext(name_spc+'StopPointName')
                    next_stop = '-'
                    departure = aim_departure
                    arrival = ''
                    delay = get_time_difference(aim_departure, exp_departure)
            else:
                recordedCalls = journey.find(name_spc+'RecordedCalls')
                lastRecordedCall = recordedCalls[-1]
            
                if not firstEstimatedCall.find(name_spc+'DepartureStatus'):
                    # Next station is terminus.
                    status = firstEstimatedCall.findtext(name_spc+'ArrivalStatus')
                    remark = ''
                    rec_departure = get_time(lastRecordedCall.findtext(name_spc+'ActualDepartureTime'))
                    aim_arrival = get_time(firstEstimatedCall.findtext(name_spc+'AimedArrivalTime'))
                    exp_arrival = get_time(firstEstimatedCall.findtext(name_spc+'ExpectedArrivalTime'))
                    last_stop = lastRecordedCall.findtext(name_spc+'StopPointName')
                    next_stop = firstEstimatedCall.findtext(name_spc+'StopPointName')
                    departure = rec_departure
                    arrival = aim_arrival
                    delay = get_time_difference(aim_arrival, exp_arrival)
                else:
                    # Middle of journey.
                    status = firstEstimatedCall.findtext(name_spc+'DepartureStatus')
                    remark = ''
                    rec_departure = get_time(lastRecordedCall.findtext(name_spc+'ActualDepartureTime'))
                    aim_arrival = get_time(firstEstimatedCall.findtext(name_spc+'AimedArrivalTime'))
                    exp_arrival = get_time(firstEstimatedCall.findtext(name_spc+'ExpectedArrivalTime'))
                    aim_departure = get_time(firstEstimatedCall.findtext(name_spc+'AimedDepartureTime'))
                    exp_departure = get_time(firstEstimatedCall.findtext(name_spc+'ExpectedDepartureTime'))
                    last_stop = lastRecordedCall.findtext(name_spc+'StopPointName')
                    next_stop = firstEstimatedCall.findtext(name_spc+'StopPointName')
                    departure = rec_departure
                    arrival = aim_arrival
                    delay = get_time_difference(aim_arrival, exp_arrival)

            single_journey = {
                'Nr':journey_count, 'Linje':line, 'Fra':origin, 'Til':destination, 
                'Med':operator, 'Avgang':last_stop, 'Kl':departure, 'Ankomst':next_stop, 
                'Kl':arrival, 'Forsinkelse':delay, 'Merknad':remark
                }
            journey_count += 1
            all_journeys.append(single_journey)
    print(all_journeys)


def get_time(timestamp: str):
    #2023-01-29T05:32:00+01:00
    timestamp = timestamp.removesuffix('+01:00')
    [date, time] = timestamp.split('T')
    [time, _] = time.rsplit(sep=':', maxsplit=1)
    return time

def get_time_difference(time1:str, time2:str):
    # time1 < time2
    time1 = time1.split(':')
    time2 = time2.split(':')
    time1 = [int(i) for i in time1]
    time2 = [int(i) for i in time2]
    delay = 60*(time2[0]-time1[0]) + (time2[1]-time1[1])
    return delay


list_of_train_dict2 = [
    {'Nr': 1, 'Linje': 'R70', 'Fra': 'Trondheim', 'Til' : 'Oslo', 'Med':'SJN', 'Neste stasjon':'Steinkjer', 'Kl':'13:32', 'Forsinkelse':'+ 3 min', 'Merknad':'Underveis'},
    {'Nr': 2, 'Linje': 'R60', 'Fra': 'Trondheim', 'Til' : 'Oslo', 'Med':'SJN', 'Neste stasjon':'Steinkjer', 'Kl':'13:32', 'Forsinkelse':'+ 3 min', 'Merknad':'Underveis'},
    {'Nr': 3, 'Linje': 'R50', 'Fra': 'Trondheim', 'Til' : 'Oslo', 'Med':'SJN', 'Neste stasjon':'Steinkjer', 'Kl':'13:32', 'Forsinkelse':'', 'Merknad':'Underveis'},
    {'Nr': 4, 'Linje': 'R40', 'Fra': 'Trondheim', 'Til' : 'Oslo', 'Med':'SJN', 'Neste stasjon':'Steinkjer', 'Kl':'13:32', 'Forsinkelse':'+ 3 min', 'Merknad':'Underveis'},
    {'Nr': 5, 'Linje': 'R30', 'Fra': 'Trondheim', 'Til' : 'Oslo', 'Med':'SJN', 'Neste stasjon':'Steinkjer', 'Kl':'13:32', 'Forsinkelse':'+ 3 min', 'Merknad':'Underveis'}
]



def get_train_table():

    # returns a list of dicts on the form [{key1:value, key2:value}, {key1:value, key2:value},]
    antall_tog = 5
    header = ['Nr', 'Linje', 'Fra', 'Til', 'Med', 'Neste stasjon', 'Kl', 'Forsinkelse', 'Merknad']



    pass



if __name__ == "__main__":
    folder='test_data/'

    """API spørring"""
    #api_str = get_api_str(interval=30, line=None, direction=None, freighttrain=False)
    #print(base_url_et+api_str)
    #xml_str = get_api_xml_str(api_str)
    #root = ET.fromstring(xml_str)

    """Saved txt"""
    #xml_str = get_saved_xml_str('sm_osl')
    #root = ET.fromstring(xml_str)
    
    """Saved xml"""
    tree = ET.parse(folder+'et_40_norge_pass.xml')
    root = tree.getroot() 

    res = root[0].findtext(name_spc+'ResponseTimestamp')
    print(res)

    pretty_print_xml(root)

    #parse_xml_tree(root)
