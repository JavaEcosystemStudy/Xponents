"""
from http://Geonames.org/export/dump

The main 'geoname' table has the following fields :
---------------------------------------------------
"""
from copy import copy

from opensextant import get_country
from opensextant.gazetteer import DataSource, get_default_db, load_stopterms
from opensextant.utility import get_list, has_cjk, has_arabic, trivial_bias, is_value, is_code, get_csv_reader, parse_float

schema = """
geonameid         : integer id of record in geonames database
name              : name of geographical point (utf8) varchar(200)
asciiname         : name of geographical point in plain ascii characters, varchar(200)
alternatenames    : alternatenames, comma separated, ascii names automatically transliterated, convenience attribute from alternatename table, varchar(10000)
latitude          : latitude in decimal degrees (wgs84)
longitude         : longitude in decimal degrees (wgs84)
feature class     : see http://www.geonames.org/export/codes.html, char(1)
feature code      : see http://www.geonames.org/export/codes.html, varchar(10)
country code      : ISO-3166 2-letter country code, 2 characters
cc2               : alternate country codes, comma separated, ISO-3166 2-letter country code, 200 characters
admin1 code       : fipscode (subject to change to iso code), see exceptions below, see file admin1Codes.txt for display names of this code; varchar(20)
admin2 code       : code for the second administrative division, a county in the US, see file admin2Codes.txt; varchar(80)
admin3 code       : code for third level administrative division, varchar(20)
admin4 code       : code for fourth level administrative division, varchar(20)
population        : bigint (8 byte int)
elevation         : in meters, integer
dem               : digital elevation model, srtm3 or gtopo30, average elevation of 3''x3'' (ca 90mx90m) or 30''x30'' (ca 900mx900m) area in meters, integer. srtm processed by cgiar/ciat.
timezone          : the iana timezone id (see file timeZone.txt) varchar(40)
modification date : date of last modification in yyyy-MM-dd format
"""
"""
AdminCodes:
Most adm1 are FIPS codes. ISO codes are used for US, CH, BE and ME. UK and Greece are using an additional level between country and fips code. The code '00' stands for general features where no specific adm1 code is defined.
The corresponding admin feature is found with the same countrycode and adminX codes and the respective feature code ADMx.

"""

GENERATED_BLOCK = 40000000
GEONAMES_SOURCE = "G"
GEONAMES_GAZ_TEMPLATE = {
    "id": "",
    "place_id": None,
    "name": None,
    "adm1": None,
    "adm2": None,
    "feat_class": None,
    "feat_code": None,
    "FIPS_cc": None,
    "cc": None,
    # Inject constant data at ingest time -- "source" = G for Geonames.org
    "source": GEONAMES_SOURCE,
    "script": None,
    # Default bias tuning
    "name_bias": 0,
    # ID Bias is not used much
    "id_bias": 0,
    "name_type": "N"
}

MAP_GN_OPENSEXTANT = {
    "geonameid": "place_id",
    "name": "name",
    "latitude": "lat",
    "longitude": "lon",
    "feature_class": "feat_class",
    "feature_code": "feat_code",
    "country_code": "cc",
    "admin1_code": "adm1",
    "admin2_code": "adm2"
}

stopterms = load_stopterms(project_dir=".")


def _format(f):
    return float("{:0.3}".format(f))


def generated_entries(geo, names):
    """
    Generate all possible entries.
    :param geo:  metadata
    :param names:  just the names in a set
    :return:
    """
    entries = []
    for n in names:
        loc = copy(geo)
        loc["name"] = n
        nt = loc["name_type"]
        if nt == "N":
            if is_code(n):
                loc["name_type"]= "C"
        if n.lower() in stopterms:
            loc["search_only"] = True
        nm_bias = trivial_bias(n)
        loc["name_bias"] = nm_bias
        grp = ""
        if has_cjk(n):
            loc["name_cjk"] = n
            grp = "cjk"
            loc["name_bias"] = _format(nm_bias + 0.10)
        elif has_arabic(n):
            loc["name_ar"] = n
            grp = "ar"
            loc["name_bias"] = _format(nm_bias + 0.10)
        loc["name_group"] = grp
        entries.append(loc)
    return entries


class GeonamesOrgGazetteer(DataSource):
    def __init__(self, dbf, **kwargs):
        DataSource.__init__(self, dbf, **kwargs)
        self.source_keys = [GEONAMES_SOURCE]
        self.source_name = "Geonames.org"

    def process_source(self, sourcefile):
        """
        :param sourcefile: Geonames allCountries source file or any other file of the same schema.
        :return: Yields geoname dict
        """
        header_names = []
        for col in schema.split("\n"):
            columns = get_list(col, delim=":")
            if columns:
                header_names.append(columns[0].replace(" ", "_"))

        # So much harder for normal mixed text/number data:
        # from pandas import read_csv
        # df = read_csv(args.geonames, delimiter="\t", header=None, names=header_names, encoding="UTF-8")

        with open(sourcefile, "r", encoding="UTF-8") as fh:
            df = get_csv_reader(fh, delim="\t", columns=header_names)
            self.purge() # Remove all previous records.
            namecount = 0
            for gn in df:
                self.rowcount += 1
                geo = copy(GEONAMES_GAZ_TEMPLATE)
                # Gather name variants
                plid = gn["geonameid"]
                names = set([])
                variants = gn["alternatenames"]
                if is_value(variants):
                    # print(variants)
                    for nm in get_list(variants, delim=","):
                        names.add(nm)
                nm = gn["asciiname"]
                if is_value(nm):
                    names.add(nm)

                for f in header_names:
                    # Gather Fields from source row and copy to destination schema.
                    k = MAP_GN_OPENSEXTANT.get(f)
                    if not k:
                        continue
                    geo[k] = gn[f]

                if "cc" not in geo:
                    print("What Country?", gn)
                    continue

                geo["place_id"] = f"G{plid}"
                cc = geo["cc"]
                C = get_country(cc)
                if C:
                    geo["FIPS_cc"] = C.cc_fips
                else:
                    print(f"Unknown code '{cc}'")
                Y,X = geo["lat"], geo["lon"]
                geo["lat"] = parse_float(Y)
                geo["lon"] = parse_float(X)
                # Avoid confusing row counts as 1 row = 1 or more names.
                _this_namecount = 0
                self.quiet = False
                for entry in generated_entries(geo, names):
                    namecount += 1
                    _this_namecount += 1
                    self.quiet = _this_namecount > 1
                    entry["id"] = GENERATED_BLOCK + namecount
                    if entry.get("search_only"):
                        self.excluded_terms.add(entry["name"])
                    yield entry


if __name__ == "__main__":
    from argparse import ArgumentParser

    ap = ArgumentParser()
    ap.add_argument("geonames")
    ap.add_argument("--db", default=get_default_db())
    ap.add_argument("--max", help="maximum rows to process for testing", default=-1)
    ap.add_argument("--debug", action="store_true", default=False)
    ap.add_argument("--optimize", action="store_true", default=False)

    args = ap.parse_args()

    source = GeonamesOrgGazetteer(args.db,     debug = args.debug)
    source.normalize(args.geonames, limit=int(args.max), optimize=args.optimize)
