import pandas as pd
from pathlib import Path

def clean_mexico_data(input_csv: str, output_csv: str = "00data.csv") -> str:
    """
    Cleans the raw Mexico mortality dataset and saves it to a CSV file.
    """

    # Load data
    df = pd.read_csv(input_csv)

    # Convert all column names to uppercase
    df.columns = df.columns.str.upper()

    # Drop invalid dates
    df = df[df['DIA_OCURR'] != 99].copy()

    # Cause of death groups
    df['IS_I'] = df['CAUSA_DEF'].str.startswith('I').astype(int)
    df['IS_J'] = df['CAUSA_DEF'].str.startswith('J').astype(int)
    df['IS_F'] = df['CAUSA_DEF'].str.startswith('F').astype(int)
    df['IS_TX'] = df['CAUSA_DEF'].isin(['T67', 'X30']).astype(int)

    # Age groups
    df['Group_A_EDAD'] = df['EDAD_AGRU'].between(1, 5, inclusive='both').astype(int)
    df['Group_B_EDAD'] = df['EDAD_AGRU'].isin([6, 7, 8]).astype(int)
    df['Group_C_EDAD'] = df['EDAD_AGRU'].between(9, 17, inclusive='both').astype(int)
    df['Group_D_EDAD'] = df['EDAD_AGRU'].between(18, 21, inclusive='both').astype(int)
    df['Group_E_EDAD'] = df['EDAD_AGRU'].between(22, 29, inclusive='both').astype(int)
    df['Group_F_EDAD'] = (df['EDAD_AGRU'] == 30).astype(int)

    # Education groups
    df['Group_A_ESCOLARIDA'] = (df['ESCOLARIDA'] == 1).astype(int)
    df['Group_B_ESCOLARIDA'] = df['ESCOLARIDA'].between(2, 7, inclusive='both').astype(int)
    df['Group_C_ESCOLARIDA'] = (df['ESCOLARIDA'] == 8).astype(int)
    df['Group_D_ESCOLARIDA'] = df['ESCOLARIDA'].isin([9, 10]).astype(int)
    df['Group_E_ESCOLARIDA'] = df['ESCOLARIDA'].isin([88, 99]).astype(int)

    # Sex groups
    df['Group_A_SEXO'] = (df['SEXO'] == 1).astype(int)  
    df['Group_B_SEXO'] = (df['SEXO'] == 2).astype(int)  
    df['Group_C_SEXO'] = (df['SEXO'] == 9).astype(int)

    #Nationality groups
    df['NACIONALID_MEXICANA'] = (df['NACIONALID'] == 1).astype(int)
    df['NACIONALID_EXTRANJERA'] = (df['NACIONALID'] == 2).astype(int)
    df['NACIONALID_NO_ESPEC'] = (df['NACIONALID'] == 9).astype(int)

    # Marital status groups
    df['CIVIL_SINGLE']       = (df['EDO_CIVIL'] == 1).astype(int)
    df['CIVIL_WIDOWED']      = (df['EDO_CIVIL'] == 3).astype(int)
    df['CIVIL_DIVORCED_SEPERATED']     = df['EDO_CIVIL'].isin([2, 6]).astype(int)
    df['CIVIL_COHABITING']   = (df['EDO_CIVIL'] == 4).astype(int)  
    df['CIVIL_MARRIED']      = (df['EDO_CIVIL'] == 5).astype(int)
    df['CIVIL_NOT_SPEC']     = (df['EDO_CIVIL'] == 9).astype(int)

    # Date of occurrence
    df['date_of_occurrence'] = pd.to_datetime(
        df[['ANIO_OCUR', 'MES_OCURR', 'DIA_OCURR']]
        .rename(columns={'ANIO_OCUR': 'year', 'MES_OCURR': 'month', 'DIA_OCURR': 'day'}),
        errors='coerce'
    )

    # Occupation groups
    df['Group_A_OCUPACION'] = df['OCUPACION'].isin(
        [1, 2, 3, 4, 5, 7, 8, 9]
    ).astype(int)
    df['Group_B_OCUPACION'] = (df['OCUPACION'] == 6).astype(int)
    df['Group_C_OCUPACION'] = df['OCUPACION'].isin([10, 11, 97, 98, 99]).astype(int)

    # Drop unused columns (list from your notebook)
    columns_to_drop = [
        'ENT_REGIS', 'MUN_REGIS', 'ENT_RESID', 'MUN_RESID', 'TLOC_RESID', 'CAUSA_DEF', 
        'LISTA_MEX', 'SEXO', 'EDAD', 'MES_REGIS', 'ANIO_REGIS', 'DIA_NACIM', 'MES_NACIM', 
        'ANIO_NACIM', 'OCUPACION', 'ESCOLARIDA', 'EDO_CIVIL', 'PRESUNTO', 'OCURR_TRAB', 
        'LUGAR_OCUR', 'NECROPSIA', 'ASIST_MEDI', 'SITIO_OCUR', 'COND_ACTIV', 'HORA_OCUR', 
        'CAPITULO', 'GRUPO', 'LISTA1', 'LISTA5', 'VIOLENCIA', 'EMBARAZO','COND_CERT','CERT_NOMED',
        'DERECHOHAB','REL_EMBA','HORAS','MINUTOS','GR_LISMEX','VIO_FAMI','EDAD_AGRU','MATERNAS',
        'DIS_RE_OAX','NACIONALID','TLOC_OCURR','DIA_REGIS','AREA_UR','COMPLICARO',
        'DIA_CERT','MES_CERT','ANIO_CERT','PESO', 'LENGUA',	'COND_ACT',	'PAR_AGRE',	'ENT_OCULES',
        'MUN_OCULES', 'LOC_RESID','LOC_OCURR','LOC_OCULES','RAZON_M','LOC_OCUR'
    ]
    df = df.drop(columns=[c for c in columns_to_drop if c in df.columns], errors='ignore')

    # Drop extra columns at the end as they are included in the date
    for col in ['DIA_OCURR', 'MES_OCURR', 'ANIO_OCUR']:
        if col in df.columns:
            df = df.drop(columns=col)

    # Drop rows where ENT_OCURR or MUN_OCURR is 999
    df = df[~((df['ENT_OCURR'] == 999) | (df['MUN_OCURR'] == 999))]

    # Move date_of_occurrence to the first column
    cols = ['date_of_occurrence'] + [c for c in df.columns if c != 'date_of_occurrence']
    df = df[cols]

    # Save cleaned dataset
    df.to_csv(output_csv, index=False)

    return str(Path(output_csv).resolve())

clean_mexico_data(
    input_csv="/Users/pratiyush/Desktop/MexicoHeatMortality/raw_data/DEFUN21.csv",
    output_csv="21data.csv"
)