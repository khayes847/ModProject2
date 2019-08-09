"""get rain info"""

def rain_table(season, api_key):
    """get Berlin rain info for specific season from Dark Skies API"""

    #establish database connection & cursor
    import sqlite3
    import zipfile
    unzippedfile = zipfile.ZipFile('footballdelphi.zip', mode = 'r')
    sqlfile = unzippedfile.extract('database.sqlite')
    conn = sqlite3.connect(sqlfile)
    c = conn.cursor()


    #get season start and end dates (narrow down API call)
    sql_query_min = """SELECT min(date) FROM Matches WHERE Season == "{}" """.format(season)
    season_start_date = c.execute(sql_query_min).fetchall()
    season_start_date = season_start_date[0][0]
    sql_query_max = """SELECT max(date) FROM Matches WHERE Season == "{}" """.format(season)
    season_end_date = c.execute(sql_query_max).fetchall()
    season_end_date = season_end_date[0][0]

    #get list of dates between beginning and end of season
    #source: https://www.w3resource.com/python-exercises/date-time-exercise/python-date-time-exercise-50.php
    from datetime import timedelta, date

    def daterange(date1, date2):
        for n in range(int ((date2 - date1).days)+1):
            yield date1 + timedelta(n)

    season_dates = []
    start_dt = date(int(season_start_date[0:4]),int(season_start_date[5:7]),int(season_start_date[8:10]))
    end_dt = date(int(season_end_date[0:4]),int(season_end_date[5:7]),int(season_end_date[8:10]))
    for dt in daterange(start_dt, end_dt):
        season_dates.append(dt.strftime("%Y-%m-%d"))

    # create dictionary of historical daily precipiation reports using DarkSkies api
    import requests
    berlin_url = "https://api.darksky.net/forecast/{}/52.5200,13.4050,{}T12:00:00"
    berlin_rain_dicts = []
    for season_date in season_dates:
        dated_url = berlin_url.format(api_key, season_date)
        result = requests.get(dated_url)
        #print(result.status_code)      #intermediary code
        temp_dict = result.json()['daily']['data'][0]
        temp_dict.update({'Date': season_date})
        if 'precipType' not in temp_dict.keys():
            temp_dict.update({'precipType': 'no precipitation'})
        #print(temp_dict)               #intermediary code
        rain_keys = ['Date', 'precipType'] #other keys that give similar data: 'summary', 'icon', 'precipIntensity'
        filtered_dict = { rain_key: temp_dict[rain_key] for rain_key in rain_keys }
        berlin_rain_dicts.append(filtered_dict)


    #create Pandas dataframe for rain data
    import pandas as pd
    berlin_rain_data = pd.DataFrame(berlin_rain_dicts)


    #query for match data for desired season and create dataframe
    sql_query_matches = """SELECT * from matches WHERE Season = "{}" """.format(season)
    c.execute(sql_query_matches)
    matches = pd.DataFrame(c.fetchall())
    matches.columns = [x[0] for x in c.description]

    #merge rain and match datatables
    matches_with_rain_data = pd.merge(matches, berlin_rain_data, how="inner", on="Date")
    rainy_matches = matches_with_rain_data[matches_with_rain_data["precipType"] == "rain"]

    return rainy_matches
