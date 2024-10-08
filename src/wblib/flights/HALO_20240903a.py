import pandas as pd
import numpy as np
import orcestra.sat
import orcestra.flightplan as fp
from orcestra.flightplan import sal, mindelo, LatLon, IntoCircle, find_ec_lon

def ec_time_at_lat(ec_track, lat):
    e = np.datetime64("2024-08-01")
    s = np.timedelta64(1, "ns")
    return (((ec_track.swap_dims({"time":"lat"}).time - e) / s).interp(lat=lat) * s + e)


def _flight_HALO_20240903a():
    flight_time = pd.Timestamp(2024, 9, 3, 12, 0, 0).tz_localize("UTC")

    radius = 72e3*1.852
    atr_radius = 38e3*1.852

    band = "east"
    airport = sal if band == "east" else bco

    # Load ec satellite track for 
    ec_track = orcestra.sat.SattrackLoader("EARTHCARE", "2024-08-29", kind="PRE").get_track_for_day(f"{flight_time:%Y-%m-%d}")
    ec_track = ec_track.sel(time=slice(f"{flight_time:%Y-%m-%d} 14:00", None))
    ec_lons, ec_lats = ec_track.lon.values, ec_track.lat.values

    # Latitudes where we enter and leave the ec track (visually estimated)
    lat_ec_north_in = 14
    lat_ec_south = 2.0

    # latitude of circle centers
    lat_c_north = 11.5
    lat_c_south = 4.0
    lat_c_south_n = lat_c_south + 1.0
    lat_c_south_s = lat_c_south - 1.0

    lat_c_mid = lat_c_south + (lat_c_north-lat_c_south)/2.0
    lat_c_mid_n = lat_c_mid + 1.0
    lat_c_mid_s = lat_c_mid - 1.0

    lat_ec_under = lat_c_north - (radius/60./1852. * np.cos(np.deg2rad(lat_c_north)))

    c_atr_nw = LatLon(17.433,-23.500, label = "c_atr")
    c_atr_se = LatLon(16.080,-21.715, label = "c_atr")

    # create ec track
    ec_north = LatLon(lat_ec_north_in, find_ec_lon(lat_ec_north_in, ec_lons, ec_lats), label = "ec_north")
    ec_south = LatLon(lat_ec_south, find_ec_lon(lat_ec_south, ec_lons, ec_lats), label = "ec_south")

    # create circles
    c_north = LatLon(lat_c_north, find_ec_lon(lat_c_north, ec_lons, ec_lats), label = "c_north")

    c_south = LatLon(lat_c_south, find_ec_lon(lat_c_south, ec_lons, ec_lats), label = "c_south")
    c_south_s = LatLon(lat_c_south_s, find_ec_lon(lat_c_south_s, ec_lons, ec_lats), label = "c_south_s")
    c_south_n = LatLon(lat_c_south_n, find_ec_lon(lat_c_south_n, ec_lons, ec_lats), label = "c_south_n")

    c_mid = LatLon(lat_c_mid, find_ec_lon(lat_c_mid, ec_lons, ec_lats), label = "c_mid")
    c_mid_s = LatLon(lat_c_mid_s, find_ec_lon(lat_c_mid_s, ec_lons, ec_lats), label = "c_mid_s")
    c_mid_n = LatLon(lat_c_mid_n, find_ec_lon(lat_c_mid_n, ec_lons, ec_lats), label = "c_mid_n")

    c_atr = c_atr_se

    # ec underpass
    ec_under = LatLon(lat_ec_under, find_ec_lon(lat_ec_under, ec_lons, ec_lats), label = "ec_under")
    ec_under = ec_under.assign(time=fp.ec_time_at_lat(ec_track, float(ec_under.lat)))

    # Define flight track
    outbound_legs = [
        airport.assign(fl=0),
        ec_north.assign(fl=410),
        ec_south.assign(fl=410),
        ]

    ec_legs = [
        IntoCircle(c_south.assign(fl=410), radius, -360),   
        IntoCircle(c_mid.assign(fl=430), radius, -360), 
        c_mid.assign(fl=430),
        ec_under.assign(fl=450),
        c_north.assign(fl=450),
        IntoCircle(c_north.assign(fl=450), radius, -360,enter=98),   
        ec_north.assign(fl=450),
        ]
    inbound_legs = [
        airport.assign(fl=350),
        IntoCircle(c_atr.assign(fl=350), atr_radius, -360), 
        airport.assign(fl=0),
        ]

    waypoints = outbound_legs + ec_legs + inbound_legs 

    waypoint_centers = []
    for point in waypoints:
        if isinstance(point, IntoCircle):
            point = point.center
        waypoint_centers.append(point)

    path = fp.expand_path(waypoints, dx=10e3)

    return flight_time, path