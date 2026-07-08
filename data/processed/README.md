# data/processed/ — folder structure

Each two-digit folder is one entidad federativa, named by its INEGI
code (the special `33` is not an INEGI code — it is the RNPDNO's "se
desconoce" bucket for records whose entidad is unknown). `all-states/`
holds national files combined from the per-state folders.

Folder contents follow the same pattern everywhere — monthly CSVs named
`YYYY-MM.csv` plus a `sin-fecha.csv` per state — and grow as more
periods are ingested. The column schema and its caveats are documented
in [`docs/data_dictionary.md`](../../docs/data_dictionary.md); read
that before quoting numbers.

| folder | entidad |
|--------|---------|
| `01` | Aguascalientes |
| `02` | Baja California |
| `03` | Baja California Sur |
| `04` | Campeche |
| `05` | Coahuila |
| `06` | Colima |
| `07` | Chiapas |
| `08` | Chihuahua |
| `09` | Ciudad de México |
| `10` | Durango |
| `11` | Guanajuato |
| `12` | Guerrero |
| `13` | Hidalgo |
| `14` | Jalisco |
| `15` | Estado de México |
| `16` | Michoacán |
| `17` | Morelos |
| `18` | Nayarit |
| `19` | Nuevo León |
| `20` | Oaxaca |
| `21` | Puebla |
| `22` | Querétaro |
| `23` | Quintana Roo |
| `24` | San Luis Potosí |
| `25` | Sinaloa |
| `26` | Sonora |
| `27` | Tabasco |
| `28` | Tamaulipas |
| `29` | Tlaxcala |
| `30` | Veracruz |
| `31` | Yucatán |
| `32` | Zacatecas |
| `33` | Entidad no especificada (RNPDNO "se desconoce" — not an INEGI code) |
| `all-states` | National files: `YYYY-MM.csv` (all states, one month) and `YYYY.csv` (all states, full year + each state's SIN_FECHA bucket) |
