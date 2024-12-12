# Import 3-party packages
import pandas as pd #Deal with dataframe 
import streamlit as st
import io 
import xmltodict
import xlsxwriter
import sqlitecloud
import pytz 
# Import standard packages
import datetime
import os

APPNAME = "XML_CONVERTER" #Web app that converts a xml invoice document into a Excel file

def display_app_title():
    """ Display program title and a short description of the app's scope """
    st.title(":blue[Working with xml invoice] :open_book:")
    st.subheader(":gray[Web app that converts a xml invoice document into a Excel file.]")
    st.markdown("Powered with Streamlit :streamlit:")
    st.divider()


def upload_xml_file() -> None:
    """ Widget used to upload an xml file """
    uploaded_file = st.file_uploader("Choose a xml b2b invoice file:", type="xml", accept_multiple_files=False)
    return uploaded_file


def display_applog() -> None:
    """ Display status and date/time when run is finished """
    appname = __file__
    local_tz = pytz.timezone('Europe/Paris')
    local_time = local_tz.localize(datetime.datetime.now())
    cpudate = local_time.strftime("%Y-%m-%d %H:%M:%S")
    st.divider()
    st.markdown(''' :orange[**APP LOG**] ''')
    st.write(" :mantelpiece_clock: :blue-background[App terminated successfully: ]", cpudate)   


def write_applog_to_sqlitecloud(log_values:dict) -> None:
    """ Write applog into SQLite Cloud Database """
    appname = __file__
    db_link = ""
    db_apikey = ""
    db_name = ""
    # Get database information
    try:
        #Search DB credentials using OS.GETENV
        db_link = os.getenv("SQLITECLOUD_DBLINK")
        db_apikey = os.getenv("SQLITECLOUD_APIKEY")
        db_name = os.getenv("SQLITECLOUD_DBNAME")
    except st.StreamlitAPIException as errMsg:
        try:
            #Search DB credentials using ST.SECRETS
            db_link = st.secrets["SQLITE_DBLINK"]
            db_apikey = st.secrets["SQLITE_APIKEY"]
            db_name = st.secrets["SQLITE_DBNAME"]
        except st.StreamlitAPIException as errMsg:
            st.write("**ERROR: DB credentials NOT FOUND")    
            st.error(f"An error occurred: {errMsg}", icon="🚨")
    
    conn_string = "".join([db_link, db_apikey])
    # Connect to SQLite Cloud platform
    try:
        conn = sqlitecloud.connect(conn_string)
    except Exception as errMsg:
        e = RuntimeError(f"**ERROR connecting to database: {errMsg}")
        st.exception(e)
    
    # Open SQLite database
    conn.execute(f"USE DATABASE {db_name}")
    cursor = conn.cursor()
    
    # Setup sqlcode for inserting applog as a new row
    sqlcode = """INSERT INTO applog (appname, applink, apparam, appstatus, appmsg, cpudate)
            VALUES (?, ?, ?, ?, ?, ?);
            """
    rome_tz = pytz.timezone('Europe/Rome')
    rome_datetime = rome_tz.localize(datetime.datetime.now()) 
    cpudate = rome_datetime.strftime("%Y-%m-%d %H:%M:%S")
    values = (log_values["appname"], log_values["applink"], log_values["apparam"], log_values["appstatus"], log_values["appmsg"], cpudate)
    try:
        cursor.execute(sqlcode, values)
    except Exception as errMsg:
        e = RuntimeError(f"**ERROR inserting new applog row: {errMsg}")
        st.exception(e)
    else:
        conn.commit()        
    finally:
        cursor.close()


def df_sum_codart(df_in: pd.DataFrame) -> pd.DataFrame:
    """ Group the amount of rows by some header/position fields """
    df_grouped = pd.DataFrame()   
    # Raggruppiamo per i campi significativi e sommiamo i valori di "prezzo unitario"
    df_grouped = df_in.groupby(["T_filein", "T_num_doc", "T_data_doc", "P_nrdisegno", "P_commessa", "P_nrddt"], as_index=False).agg({"P_prezzo_tot": "sum"})
    # Rinominiamo la colonna "P_prezzo_tot" in "P_importo"
    df_grouped = df_grouped.rename(columns={"P_prezzo_tot": "P_importo"})
    df_grouped["P_importo"] = df_grouped["P_importo"].round(2)
    return df_grouped


def parse_xml(uploaded_file, grouping_opt) -> pd.DataFrame:
    """ Function that parses an XMLB2B file (invoice) and returns a dataframe containing the most important informations of the documents"""
    # Inizialize variables
    t_piva_mitt = list()
    t_ragsoc_mitt = list()
    t_tipo_doc = list()
    t_num_doc = list()
    t_data_doc = list()
    t_importo_doc = list()
    p_nr_linea = list()
    p_codart = list()
    p_qta = list()
    p_um = list()
    p_przunit = list()
    p_desc_linea = list()
    p_prezzo_tot = list()
    p_codiva = list()
    p_tiponota = list()
    p_descnota = list()
    p_nrdisegno = list()
    p_commessa = list()
    p_nrddt = list()

    # To convert to a string based IO:
    stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
    #st.write(stringio)

    # To read file as string:
    string_data = stringio.read()
    
    # Trasform xml file into dictionary
    xml_dict = xmltodict.parse(string_data)
    
    tag_root = list(xml_dict.keys())[0]

    # Extract data from FatturaElettronicaHeader
    try:
        tag_piva_mitt = xml_dict[tag_root]["FatturaElettronicaHeader"]["CedentePrestatore"]["DatiAnagrafici"]["IdFiscaleIVA"]["IdCodice"]
    except KeyError:
        tag_piva_mitt = "**"
    t_piva_mitt.append(tag_piva_mitt)

    try:
        tag_ragsoc_mitt = xml_dict[tag_root]["FatturaElettronicaHeader"]["CedentePrestatore"]["DatiAnagrafici"]["Anagrafica"]["Denominazione"]
    except KeyError:
        tag_ragsoc_mitt = "**"
    t_ragsoc_mitt.append(tag_ragsoc_mitt)


    # Extract data from FatturaElettronicaBody - DatiGenerali
    try:
        tag_tipo_doc = xml_dict[tag_root]["FatturaElettronicaBody"]["DatiGenerali"]["DatiGeneraliDocumento"]["TipoDocumento"]
    except KeyError:
        tag_tipo_doc = "**"
    t_tipo_doc.append(tag_tipo_doc)

    try:
        tag_data_doc = xml_dict[tag_root]["FatturaElettronicaBody"]["DatiGenerali"]["DatiGeneraliDocumento"]["Data"]
    except KeyError:
        tag_data_doc = "**"
    t_data_doc.append(tag_data_doc)

    try:
        tag_num_doc = xml_dict[tag_root]["FatturaElettronicaBody"]["DatiGenerali"]["DatiGeneraliDocumento"]["Numero"]
    except KeyError:
        tag_num_doc = "**"
    t_num_doc.append(tag_num_doc)

    try:
        tag_importo_doc = xml_dict[tag_root]["FatturaElettronicaBody"]["DatiGenerali"]["DatiGeneraliDocumento"]["ImportoTotaleDocumento"]
    except KeyError:
        tag_importo_doc = "**"
    t_importo_doc.append(tag_importo_doc)

    # Extract data from FatturaElettronicaBody - DatiBeniServizi
    lines = xml_dict[tag_root]["FatturaElettronicaBody"]["DatiBeniServizi"]["DettaglioLinee"]
    for line in lines:
        try:
            tag_nr_linea = line["NumeroLinea"]
        except KeyError:
            tag_nr_linea = "**"    
        p_nr_linea.append(tag_nr_linea)
        
        try:
            tag_codart = line["CodiceArticolo"]["CodiceValore"]
        except KeyError:
            tag_codart = "**"    
        p_codart.append(tag_codart)     

        try:
            tag_desc_linea = line["Descrizione"]
        except KeyError:
            tag_desc_linea = "**"
        p_desc_linea.append(tag_desc_linea) 

        try:
            tag_qta = line["Quantita"]
        except KeyError:
            tag_qta = "0"    
        p_qta.append(tag_qta)     
        
        try:
            tag_um = line["UnitaMisura"]
        except KeyError:
            tag_um = "**"
        p_um.append(tag_um)        
        
        try:
            tag_przunit = line["PrezzoUnitario"]
        except KeyError:
            tag_przunit = "0"
        p_przunit.append(tag_przunit)   

        try:
            tag_prezzo_tot = line["PrezzoTotale"]
        except KeyError:
            tag_prezzo_tot = "0"
        p_prezzo_tot.append(tag_prezzo_tot) 

        try:
            tag_codiva = line["AliquotaIVA"]
        except KeyError:
            tag_codiva = "0"
        p_codiva.append(tag_codiva) 

        if "AltriDatiGestionali" in line:
            lista_allegati = line["AltriDatiGestionali"]
            tag_nrdisegno = "**"
            tag_commessa = "**"
            tag_nrddt = "**"
            for allegati in lista_allegati:
                if allegati["TipoDato"] == "DISEGNO":
                    tag_nrdisegno = allegati["RiferimentoTesto"]
                elif allegati["TipoDato"] == "COMMESSA":
                    tag_commessa = allegati["RiferimentoTesto"]
                elif allegati["TipoDato"] == "N01":
                    tag_nrddt = allegati["RiferimentoTesto"]
        else:
            tag_nrdisegno = "**"
            tag_commessa = "**"
            tag_nrddt = "**"    
        p_nrdisegno.append(tag_nrdisegno)
        p_commessa.append(tag_commessa)
        p_nrddt.append(tag_nrddt)

    # Adjust lists size in order to have the same number of elements   
    nr_lines = len(p_nr_linea)
    if nr_lines != 0:    
        t_piva_mitt = t_piva_mitt * nr_lines
        t_ragsoc_mitt = t_ragsoc_mitt * nr_lines
        t_num_doc = t_num_doc * nr_lines
        t_data_doc = t_data_doc * nr_lines
        t_importo_doc = t_importo_doc * nr_lines
        t_filename = [uploaded_file.name] * nr_lines

    # Create the dataframe
    df_out = pd.DataFrame({'T_filein': t_filename,
                           'T_piva_mitt': t_piva_mitt,
                           'T_ragsoc_mitt': t_ragsoc_mitt,
                           'T_num_doc': t_num_doc,
                           'T_data_doc': t_data_doc,
                           'T_importo_doc': t_importo_doc,
                           'P_nr_linea': p_nr_linea,
                           'P_codart': p_codart,
                           'P_desc_linea': p_desc_linea,
                           'P_qta': p_qta,
                           'P_um': p_um,
                           'P_przunit': p_przunit,
                           'P_prezzo_tot': p_prezzo_tot,
                           'P_nrdisegno': p_nrdisegno,
                           'P_commessa': p_commessa,
                           'P_nrddt': p_nrddt,
                           })
    # Convert some columns into float data type
    df_out['T_importo_doc'] = df_out['T_importo_doc'].astype(float)
    df_out['P_qta'] = df_out['P_qta'].astype(float)
    df_out['P_przunit'] = df_out['P_przunit'].astype(float)
    df_out['P_prezzo_tot'] = df_out['P_prezzo_tot'].astype(float)
    
    # Grouping if option is active
    if grouping_opt:
        df_out = df_sum_codart(df_out)
    # Apply your style to desired columns    
#    df_out = df_out.style.format(precision=2, thousands='', decimal=',')
    
    return df_out


def onSearch(opt=None):
    """ Function that modify the session state when clicked by user"""
    st.session_state["clicked"] = True

def main() -> None:
    """ Main function """
    # Display app title
    display_app_title()
    st.markdown(''' :orange[**INPUT PARAMETERS**] ''')
    uploaded_file = upload_xml_file()
    grouping_opt = st.toggle("Activate grouping feature")
    
    if "clicked" not in st.session_state:
        st.session_state["clicked"] = False

    if uploaded_file is None:
        st.button("Run", icon="🔥", disabled=True)
    else:
        st.button("Run", icon="🔥", disabled=False, on_click= onSearch)   
    
    if st.session_state["clicked"]:
        if uploaded_file is not None:
            df = parse_xml(uploaded_file, grouping_opt)
            st.divider()
            st.markdown(''' :orange[**OUTPUT INFO**] ''')
            st.write("--> :green[Output dataframe records: ]",len(df))            
            st.dataframe(df, hide_index=False)
            if len(df) > 0:
                buffer = io.BytesIO()
                # Create a Pandas Excel writer using XlsxWriter as the engine.
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    # Write each dataframe to a different worksheet.
                    df.to_excel(writer, sheet_name="Invoice")
                    # Close the Pandas Excel writer and output the Excel file to the buffer
                    writer.close()
                fileout_name = uploaded_file.name.replace(".xml",".xlsx")
                st.download_button(
                    label="Download Excel",
                    data=buffer,
                    file_name=fileout_name,
                    mime="application/vnd.ms-excel",
                    icon="⏬"        
                )
            display_applog()
            log_values = dict()
            log_values["appname"] = APPNAME
            log_values["applink"] = __file__
            log_values["apparam"] = uploaded_file.name
            log_values["appstatus"] = "COMPLETED"
            log_values["appmsg"] = " "
            write_applog_to_sqlitecloud(log_values)

if __name__ == "__main__":
    main()
