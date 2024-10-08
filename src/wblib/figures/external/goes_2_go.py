from goes2go.data import goes_nearesttime, goes_latest
import matplotlib
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import pandas as pd
import xarray as xr
import seaborn as sns

from wblib.figures.briefing_info import INTERNAL_FIGURE_SIZE, ORCESTRA_DOMAIN
from wblib.figures.sattrack import plot_sattrack
from wblib.flights.flighttrack import plot_python_flighttrack
from wblib.flights.flighttrack import get_python_flightdata
from wblib.flights._define_flights import FLIGHTS

from wblib.figures.meteor_pos import plot_meteor_position

def yesterdays_goes2go_image(
        current_time: pd.Timestamp,
        briefing_time: pd.Timestamp,
        sattracks_fc_time: pd.Timestamp,
        current_location: str,
        meteor_track: xr.Dataset,
        ):
    yesterday = briefing_time - pd.Timedelta("12h")
    goes_data_yesterday = _get_goes2go_data(yesterday)
    figure = plot_goes2go_satimage(goes_data_yesterday, yesterday,
                                   sattracks_fc_time, yesterday,
                                   meteor_track)
    return figure


def latest_goes2go_image(
        current_time: pd.Timestamp,
        briefing_time: pd.Timestamp,
        sattracks_fc_time: pd.Timestamp,
        current_location: str,
        meteor_track: xr.Dataset,
        ) -> Figure:
    goes_data_latest = _get_goes2go_data_latest()
    figure = plot_goes2go_satimage(goes_data_latest, briefing_time,
                                   sattracks_fc_time, current_time,
                                   meteor_track)
    return figure


def _get_goes2go_data(
        time: pd.Timestamp
        ) -> xr.Dataset:
    time_sat = time.strftime('%Y-%m-%dT%H:%M%:%S')
    return goes_nearesttime(time_sat, satellite=16, product="ABI", domain = "F")


def _get_goes2go_data_latest() -> xr.Dataset:
    return goes_latest(satellite=16, product="ABI", domain = "F")


def _create_GOES_variable(
        goes_object: xr.Dataset, variable: str, gamma:float = 1.2
        ):
    GOES_PRODUCT_DICT = {
        "AirMass": goes_object.rgb.AirMass,
        "AirMassTropical": goes_object.rgb.AirMassTropical,
        "AirMassTropicalPac": goes_object.rgb.AirMassTropicalPac,
        "Ash": goes_object.rgb.Ash,
        "DayCloudConvection": goes_object.rgb.DayCloudConvection,
        "DayCloudPhase": goes_object.rgb.DayCloudPhase,
        "DayConvection": goes_object.rgb.DayConvection,
        "DayLandCloud": goes_object.rgb.DayLandCloud,
        "DayLandCloudFire": goes_object.rgb.DayLandCloudFire,
        "DaySnowFog": goes_object.rgb.DaySnowFog,
        "DifferentialWaterVapor": goes_object.rgb.DifferentialWaterVapor,
        "Dust": goes_object.rgb.Dust,
        "FireTemperature": goes_object.rgb.FireTemperature,
        "NaturalColor": goes_object.rgb.NaturalColor(gamma=gamma),
        "NightFogDifference": goes_object.rgb.NightFogDifference,
        "NighttimeMicrophysics": goes_object.rgb.NighttimeMicrophysics,
        "NormalizedBurnRatio": goes_object.rgb.NormalizedBurnRatio,
        "RocketPlume": goes_object.rgb.RocketPlume,
        "SeaSpray": goes_object.rgb.SeaSpray(gamma=gamma),
        "SplitWindowDifference": goes_object.rgb.SplitWindowDifference,
        "SulfurDioxide": goes_object.rgb.SulfurDioxide,
        "TrueColor": goes_object.rgb.TrueColor(gamma=gamma),
        "WaterVapor": goes_object.rgb.WaterVapor,
    }
    return GOES_PRODUCT_DICT[variable]


def plot_goes2go_satimage(
        goes_object: xr.Dataset,
        briefing_time: pd.Timestamp,
        sattracks_fc_time: pd.Timestamp,
        meteor_time: pd.Timestamp,
        meteor_track: xr.Dataset,
        goes_variable: str="TrueColor",
        ) -> Figure:
    sns.set_context("talk")
    fig, ax = plt.subplots(
        figsize=INTERNAL_FIGURE_SIZE,
        subplot_kw={"projection": ccrs.PlateCarree()}
    )
    ax.set_global()
    ax.coastlines()
    goes_variable = _create_GOES_variable(goes_object, goes_variable)
    ax.imshow(goes_variable, transform=goes_object.rgb.crs, regrid_shape=3500,
              interpolation='nearest') 
    ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False,
                 alpha = 0.25)
    ax.set_extent(ORCESTRA_DOMAIN)
    plt.title(f"Valid time: {str(goes_object.t.values)[:19]} UTC", pad=15)
    plot_sattrack(ax, briefing_time, "00H", sattracks_fc_time,
                  which_orbit="descending")
    for flight_id in FLIGHTS:
        flight = get_python_flightdata(flight_id)
        plot_python_flighttrack(flight, briefing_time, "00H", ax,
                                color="C1", show_waypoints=False)
    plot_meteor_position(meteor_time, ax, meteor=meteor_track)
    matplotlib.rc_file_defaults()
    return fig


if __name__ == "__main__":
    from orcestra.meteor import get_meteor_track

    # test get_latest_goes2go_image()
    sattracks_fc_time = pd.Timestamp(2024, 8, 5).tz_localize("UTC")
    briefing_time = pd.Timestamp(2024, 8, 11).tz_localize("UTC")
    current_time = pd.Timestamp(2024, 8, 11, 9, 30).tz_localize("UTC")
    meteor_track = get_meteor_track(deduplicate_latlon=True)

    fig = latest_goes2go_image(
        current_time, briefing_time, sattracks_fc_time, meteor_track
        )

    # test get_yesterdays_goes2go_image()
    sattracks_fc_time = pd.Timestamp(2024, 8, 5).tz_localize("UTC")
    briefing_time = pd.Timestamp(2024, 8, 12).tz_localize("UTC")
    current_time = pd.Timestamp(2024, 8, 12, 9, 30).tz_localize("UTC")
    meteor_track = get_meteor_track(deduplicate_latlon=True)

    fig = yesterdays_goes2go_image(
        current_time, briefing_time, sattracks_fc_time, meteor_track
        )