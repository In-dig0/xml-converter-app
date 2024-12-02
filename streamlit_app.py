# Import 3-party packages
import pandas as pd #Deal with dataframe 
import streamlit as st
# from lxml import etree #Parse XML files
import xmltodict

def display_app_title():
    st.title(":blue[Working with xml invoice] :open_book:")
    st.subheader(":gray[Web app that converts a xml invoice document into a csv file.]")
    st.markdown("Powered with Streamlit :streamlit:")

def upload_xml_file():
    uploaded_file = st.file_uploader("Choose a xml b2b invoice file:", type="xml", accept_multiple_files=False)
    return uploaded_file

def df_sum_codart(df_in: pd.DataFrame) -> pd.DataFrame:
    """ Function that searches keywords in a columnn_list of the dataframe df and returns the dataframe filtered"""
    df_grouped = pd.DataFrame()   
    # Raggruppiamo per i campi significativi e sommiamo i valori di "prezzo unitario"
    df_grouped = df_in.groupby(["T_filein", "T_num_doc", "T_data_doc", "P_nrdisegno"], as_index=False).agg({"P_prezzo_tot": "sum"})
    # Rinominiamo la colonna "P_prezzo_tot" in "P_importodisegno"
    df_grouped = df_grouped.rename(columns={"P_prezzo_tot": "P_importodisegno"})
    df_grouped["P_importodisegno"] = df_grouped["P_importodisegno"].round(2)
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
    p_nrddt = list()

    # Open xml file
    # with open(file_input, mode = "r", encoding="utf-8") as f:
    #    xml_string = f.read()

    # To convert to a string based IO:
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    #st.write(stringio)

    # To read file as string:
    string_data = stringio.read()
    #st.write(string_data)
    
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
            tag_nrddt = "**"
            for allegati in lista_allegati:
                if allegati["TipoDato"] == "DISEGNO":
                    tag_nrdisegno = allegati["RiferimentoTesto"]   
                elif allegati["TipoDato"] == "N01":
                    tag_nrddt = allegati["RiferimentoTesto"]
        else:
            tag_nrdisegno = "**"
            tag_nrddt = "**"    
        p_nrdisegno.append(tag_nrdisegno)       
        p_nrddt.append(tag_nrddt)

    # Adjust lists size for having the same number of elements   
    nr_lines = len(p_nr_linea)
    if nr_lines != 0:         
        t_piva_mitt = t_piva_mitt * nr_lines
        t_ragsoc_mitt = t_ragsoc_mitt * nr_lines
        t_num_doc = t_num_doc * nr_lines
        t_data_doc = t_data_doc * nr_lines
        t_importo_doc = t_importo_doc * nr_lines


    # Create the dataframe
    df_out = pd.DataFrame({'T_piva_mitt': t_piva_mitt,
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
                           'P_nrddt': p_nrddt,
                           })
    # Convert some columns into float data type
    df_out['T_importo_doc'] = df_out['T_importo_doc'].astype(float)
    df_out['P_qta'] = df_out['P_qta'].astype(float)
    df_out['P_przunit'] = df_out['P_przunit'].astype(float)
    df_out['P_prezzo_tot'] = df_out['P_prezzo_tot'].astype(float)
    df_out['T_filein'] = file_input
    
    # Grouping if option is active
    if grouping_opt:
        df_out = df_sum_codart(df_out)
    # Apply your style to desired columns    
#    df_out = df_out.style.format(precision=2, thousands='', decimal=',')
    
    return df_out

def onSearch(opt=None):
    st.session_state["clicked"] = True

#@st.cache_data
def csv_convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
#    return df.to_csv().encode("utf-8")    
    return df.to_csv(header=True, index=False, sep=';', decimal= ",")
    
if __name__ == "__main__":
    display_app_title()
    st.divider()
    st.markdown(''' :orange[**INPUT FILE**] ''')
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
            st.write("--> :green[Number of record of output dataframe: ]",len(df))            
            st.dataframe(df, hide_index=False)
            csv_data = csv_convert_df(df)
            csv_name = "export_df.csv"
            if len(df) > 0:
                st.download_button(
                    label="Download as CSV",
                    data=csv_data,
                    file_name=csv_name,
                    mime="text/csv",
                    icon="🔽"
                )            


