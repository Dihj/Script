##########################################################################################
############### To Convert CFT monthly data format to CPTv10 format   ####################
###############                  Dihj Jan 2024                        ####################
##########################################################################################
##########################################################################################
import pandas as pd
import numpy as np
import sys

SEASON_MONTHS = {
    "NDJ": [11, 12, 1],
    "DJF": [12, 1, 2],
    "JFM": [1, 2, 3],
    "FMA": [2, 3, 4],
    "MAM": [3, 4, 5],
    "AMJ": [4, 5, 6], 
    "MJJ": [5, 6, 7],
    "JJA": [6, 7, 8],
    "JAS": [7, 8, 9],
    "ASO": [8, 9, 10],
    "SON": [9, 10, 11],
    "OND": [10, 11, 12],
}
def season_to_months(season):
    return SEASON_MONTHS.get(season, [])
def calculate_seasonal_accum(df, months, season):
    results = []
    available_years = set(df["Year"].unique())
    last_year = max(available_years)  # Get the last available year
    for _, row in df.iterrows():
        year = row["Year"]
        lat = row["Lat"]
        lon = row["Lon"]

        if season in ["DJF", "NDJ"]:  # Spanning two years
            # Skip processing if next year doesn't exist in the available years
            if year == last_year and (year + 1) in available_years:
                continue  # Skip this year+1 if not exist in data
            values = []
            for month in months:
                if month in [11, 12]:  # for NDJ or DJF
                    month_name = pd.Timestamp(year=year, month=month, day=1).strftime("%b")
                    values.append(row[month_name])
                elif month == 1:
                    next_year = year + 1
                    if next_year in available_years:  
                        month_name = pd.Timestamp(year=next_year, month=month, day=1).strftime("%b")
                        values.append(df.loc[(df["Year"] == next_year), month_name].values[0])
                    else:
                        values.append(np.nan)  # If next year is not available, append NaN
                elif month == 2:  # Use next year's data (check if next year is available)
                    next_year = year + 1
                    if next_year in available_years:  # Only include next year's data if it's available
                        month_name = pd.Timestamp(year=next_year, month=month, day=1).strftime("%b")
                        values.append(df.loc[(df["Year"] == next_year), month_name].values[0])
                    else:
                        values.append(np.nan)  # If next year is not available, append NaN
            if len(values) == 3:  # Ensure all months are available for the season
                if any(np.isnan(value) for value in values):  # If missing, append NaN
                    seasonal_accum = np.nan  
                else:
                    seasonal_accum = np.nansum(values)  # Calculate accumulation
                    seasonal_accum = round(seasonal_accum, 2)
                t_value = f"{year}-{months[0]:02d}/{year + 1}-{months[-1]:02d}"  # Format
                results.append({"T": t_value, "Year": year, "Value": seasonal_accum, "Lat": lat, "Lon": lon})

        else:  # For non-shifted seasons
            values = []
            for month in months:
                month_name = pd.Timestamp(year=year, month=month, day=1).strftime("%b")
                if month_name in df.columns:
                    values.append(row[month_name])
                else:
                    values.append(np.nan)  # Add NaN if the month is missing from the data
            if len(values) == len(months):  # Ensure we have all months for the season
                if any(np.isnan(value) for value in values):  # Check for missing data
                    seasonal_accum = np.nan  # Set to NaN if any value is missing
                else:
                    seasonal_accum = np.nansum(values)  # Calculate accumulation
                    seasonal_accum = round(seasonal_accum, 2)
                t_value = f"{year}-{months[0]:02d}/{year}-{months[-1]:02d}"  # Format
                results.append({"T": t_value, "Year": year, "Value": seasonal_accum, "Lat": lat, "Lon": lon})
    return pd.DataFrame(results)
    
def main():
    if len(sys.argv) != 4:
        print("-----------------------")
        print("To run this function, ")
        print("Open your Anaconda terminal, then activate your PyCPT environment, then write:")
        print("python convert_CFT_to_CPT_format.py <your_input_csv_file> <season> <your_output_file>")
        print("------------------------")
        sys.exit(1)

    input_csv, selected_period, output_file = sys.argv[1], sys.argv[2], sys.argv[3]
    missing_value = ["-999.9", "-9999", "-999", "-99.9", ""]
    # Load the input CSV file
    #df = pd.read_csv(input_csv)
    df = pd.read_csv(input_csv, na_values=missing_value)
    #df[df < 0] = np.nan

    # Ensure required columns are present
    required_columns = ["ID", "Lat", "Lon", "Year"] + [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"CSV file must contain the columns: {required_columns}")

    # Process data based on the selected period
    if selected_period in SEASON_MONTHS.keys():  # Seasonal selection
        months = season_to_months(selected_period)
        df_grouped = calculate_seasonal_accum(df, months, selected_period)
    elif selected_period.capitalize() in df.columns:  # Single month selection
        df_grouped = df[["Year", selected_period.capitalize(), "Lat", "Lon"]].rename(columns={selected_period.capitalize(): "Value"})
        df_grouped["T"] = df_grouped["Year"].astype(str) + "-" + selected_period.capitalize()
    else:
        raise ValueError(f"Invalid period: {selected_period}. Use a valid season for example DJF, JFM, FMA etc...")

    # Check if 'Lat' and 'Lon' columns are present in the grouped data
    if 'Lat' not in df_grouped.columns or 'Lon' not in df_grouped.columns:
        raise ValueError("Ensure you have CFT data format as input data.")
    # Convert negative values to missing
    df_grouped.loc[df_grouped["Value"] < 0, "Value"] = np.nan
    # Filter out rows with NaN values in the 'Value' column
    df_grouped = df_grouped.dropna(subset=["Value"])

    # Pivot the data to CPT format
    cpt_df = df_grouped.pivot_table(
        index="T",
        columns=["Lat", "Lon"],
        values="Value"
    )

    # Ensure there are no empty rows in the pivoted data
    #cpt_df = cpt_df.dropna(how="all")
    cpt_df = cpt_df.fillna(-999.9)
    missing_value = "-999.9"
    cpt_df.columns = [f"{round(lat, 3)},{round(lon, 3)}" for lat, lon in cpt_df.columns]

    # Construct CPT header metadata
    header = [
        "xmlns:cpt=http://iri.columbia.edu/CPT/v10/",
        f"cpt:nfields=1",
        "cpt:T\t" + "\t".join(map(str, cpt_df.index)),
        f"cpt:field=prcp, cpt:nrow={len(cpt_df.index)}, cpt:ncol={len(cpt_df.columns)}, cpt:row=T, cpt:col=station, cpt:units=mm, cpt:missing={missing_value}"
    ]

    # Generate station metadata
    station_id = "\t".join(map(str, df["ID"].unique()))
    lon_values = "\t".join(map(str, df_grouped["Lon"].unique()))
    lat_values = "\t".join(map(str, df_grouped["Lat"].unique()))
    elev_values = "\t".join([""] * len(df_grouped["Lat"].unique()))
    station_names = "\t".join(map(str, df["ID"].unique()))

    stations = [
        f"\t{station_id}",
        f"cpt:X\t{lon_values}",
        f"cpt:Y\t{lat_values}",
        f"cpt:elev\t{elev_values}",
        f"cpt:Name\t{station_names}"
    ]
    output_file = f"{output_file}.tsv"
    # Save the CPT format data
    with open(output_file, "w", newline="") as f:
        # Write header and metadata
        f.write("\n".join(header) + "\n")
        f.write("\n".join(stations) + "\n")
        # Write data
        cpt_df.to_csv(f, sep="\t", index_label="T", header=False)

    print(f"CPT format data saved to {output_file}")
if __name__ == "__main__":
    main()
