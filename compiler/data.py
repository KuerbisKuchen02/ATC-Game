import csv


class Airline:
    def __init__(self, name: str, iata: str, icao: str, callsign: str, country: str, active: bool):
        self.name: str = name if name != "" else None
        self.iata: str = iata if name != "" else None
        self.icao: str = icao if name != "" else None
        self.callsign: str = callsign if name != "" else None
        self.country: str = country if name != "" else None
        self.active: bool = active


airlines: list[Airline] = []
index: dict[str, int] = {}


def load_airlines():
    global airlines
    if len(airlines) != 0:
        return
    with open("resources/airlines.csv", newline='') as csvfile:
        rows = csv.reader(csvfile, delimiter=',')
        for row in rows:
            airlines.append(Airline(row[0], row[1], row[2], row[3], row[4], True if row[5] == "Y" else False))


def index_airlines():
    global index
    global airlines
    if len(index) != 0:
        return
    index = {airline.callsign.lower(): i for i, airline in airlines}


def get_airline_from_callsign(callsign: str) -> Airline | None:
    load_airlines()
    index_airlines()
    return airlines[index[callsign]]
