from urllib.request import urlopen
import io
import numpy as np
import pandas as pd


arr = range(30)

regions=[101,147,155,185,165,151,153,157,159,161,163,167,169,183,173,175,187,201,240,210,250,190,270,260,217,219,223,230,400,411,253,259,350,265,269,320,376,316,326,360,370,306,329,330,340,336,390,420,430,440,482,410,480,450,461,479,492,530,561,563,607,510,621,540,550,573,575,630,580,710,766,615,707,727,730,741,740,746,706,751,657,661,756,665,760,779,671,791,810,813,860,849,825,846,773,840,787,820,851]

def get_chunk(regions_from, regions_to):
	regions_from = ",".join(regions_from)
	regions_to = ",".join(regions_to)
	response = urlopen((
		"https://api.statbank.dk/v1/data/FLY66/CSV?"
		f"TILKOMMUNE={regions_from}"
		f"&FRAKOMMUNE={regions_to}"
		"&ALDER=*"
		"&Tid=2018,2019,2020,2021,2022"
	))
	result_str = io.StringIO(response.read().decode("UTF-8"))
	return pd.read_csv(result_str, sep=";")

result = []
for regions_from in np.array_split(regions, 8):
	for region_to in np.array_split(regions, 8):
		regions_from_str = list(map(lambda i: str(i), regions_from.tolist()))
		regions_to_str = list(map(lambda i: str(i), region_to.tolist()))
		print(
			"Fetching data from:",
			regions_from_str[0],
			"-",
			regions_from_str[-1],
			" to ",
			regions_to_str[0],
			"-",
			regions_to_str[-1],
		)
		result.append(get_chunk(regions_from_str, regions_to_str))

df = pd.concat(result)
df.to_csv("data/DK_data_migration.csv", index=False)
