"""Static catalogs: entidades, categorías, sexo.

Entidad codes/names are INEGI codes as used by the dashboard's estado
dropdown (verified identical). Municipio catalogs are dynamic and are
fetched per state via POST /Catalogo/Municipios (see ingest.py).
"""

# INEGI code -> name, verbatim from the dashboard's cboEstado options.
ENTIDADES = {
    "1": "AGUASCALIENTES",
    "2": "BAJA CALIFORNIA",
    "3": "BAJA CALIFORNIA SUR",
    "4": "CAMPECHE",
    "5": "COAHUILA",
    "6": "COLIMA",
    "7": "CHIAPAS",
    "8": "CHIHUAHUA",
    "9": "CIUDAD DE MEXICO",
    "10": "DURANGO",
    "11": "GUANAJUATO",
    "12": "GUERRERO",
    "13": "HIDALGO",
    "14": "JALISCO",
    "15": "ESTADO DE MEXICO",
    "16": "MICHOACAN",
    "17": "MORELOS",
    "18": "NAYARIT",
    "19": "NUEVO LEON",
    "20": "OAXACA",
    "21": "PUEBLA",
    "22": "QUERETARO",
    "23": "QUINTANA ROO",
    "24": "SAN LUIS POTOSI",
    "25": "SINALOA",
    "26": "SONORA",
    "27": "TABASCO",
    "28": "TAMAULIPAS",
    "29": "TLAXCALA",
    "30": "VERACRUZ",
    "31": "YUCATAN",
    "32": "ZACATECAS",
    # Dashboard's "SE DESCONOCE" bucket (not an INEGI code): records
    # whose entidad is unknown. Included as its own entity — unknown
    # location != zero, same principle as SIN_FECHA (DECISIONS.md #8).
    "33": "ENTIDAD NO ESPECIFICADA",
}

# categoria label -> idEstatusVictima filter value. This is the finest
# categoria partition the API offers at municipio x sexo grain; the
# three values partition TotalGlobal (see docs/data_dictionary.md).
CATEGORIAS = {
    "DESAPARECIDA_O_NO_LOCALIZADA": "7",
    "LOCALIZADA_CON_VIDA": "2",
    "LOCALIZADA_SIN_VIDA": "3",
}

# Which Totales field each categoria must reconcile against.
CATEGORIA_TOTALES_FIELD = {
    "DESAPARECIDA_O_NO_LOCALIZADA": "TotalDesaparecidos",
    "LOCALIZADA_CON_VIDA": "TotalLocalizadosCV",
    "LOCALIZADA_SIN_VIDA": "TotalLocalizadosSV",
}


def cve_entidad(id_estado: str) -> str:
    """INEGI 2-digit entidad key, e.g. '1' -> '01'."""
    return id_estado.zfill(2)


def cve_municipio(id_estado: str, id_municipio: int) -> str:
    """INEGI 5-digit municipio key, e.g. ('1', 5) -> '01005'."""
    return cve_entidad(id_estado) + str(id_municipio).zfill(3)
