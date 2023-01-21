import pandas as pd
import pandasql as ps

if __name__ == '__main__':
    flights = pd.read_csv("../candidateEvalData/flights.csv")
    airports = pd.read_csv("../candidateEvalData/airports.csv")
    weather = pd.read_csv("../candidateEvalData/weather.csv")
    airlines = pd.read_csv("../candidateEvalData/airlines.csv")

    flights_with_airlines_q = """
                SELECT
                	f.arr_time,
                	f.origin,
                	f.dest,
                	a.name
                FROM
                	flights f
                INNER JOIN airlines a ON
                	f.carrier = a.carrier"""
    flights_with_airlines= ps.sqldf(flights_with_airlines_q, locals())
    print(flights_with_airlines)
    jetBlue_q = """
                SELECT
                	*
                FROM
                	flights_with_airlines f
                WHERE f.name like('%JetBlue%')
                """
    jetBlue = ps.sqldf(jetBlue_q, locals())
    print(jetBlue)
    jet_blue_by_origin_q = """
                SELECT
                	origin, count(*) "numFlights"
                FROM
                	jetBlue j
                GROUP BY j.origin
                ORDER BY numFlights
                """
    jet_blue_by_origin = ps.sqldf(jet_blue_by_origin_q, locals())
    print(jet_blue_by_origin)
    moret_than_100_flights_q = """
                    SELECT
                    	*
                    FROM
                    	jet_blue_by_origin j
                    WHERE numFlights>100
                    """
    moret_than_100_flights_ = ps.sqldf(moret_than_100_flights_q, locals())
    print(moret_than_100_flights_)

