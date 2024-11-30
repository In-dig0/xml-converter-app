# Import 3-party packages
import pandas as pd #Deal with dataframe 
import streamlit as st
from lxml import etree #Parse XML files

def display_app_title():
    st.title(":blue[Working with xml invoice] :open_book:")
    st.subheader(":gray[Web app that converts a b2b xml invoice file into a csv file, extracting only positions.]")
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


def parse_xml(file_input, grouping_opt):
    """ Function that parses an XMLB2B file (invoice) and returns a dataframe containing the most important informations of the documents"""
    # Inizialize variables
    df_out = pd.DataFrame()
    t_filein = list()
    t_prog_invio = list()
    t_fatt_b2b = list()
    t_piva_mitt = list()
    t_desc_mitt = list()    
    t_num_doc= list()
    t_data_doc = list()
    t_importo_doc = list()
    t_causale = list()
    d_nr_linea = list()
    d_codart = list()
    d_qta = list()
    d_um = list()
    d_przunit = list()
    d_desc_linea = list()
    d_prezzo_tot= list()
    d_tiponota = list()
    d_descnota = list()
    d_nrdisegno = list()
    d_rifdoc = list()
    # Parser instance
    parser = etree.XMLParser()
    try:
        tree = etree.parse(file_input, parser)
    except Exception as errMsg:
        print(f'**Error XML format file {file_input}: {errMsg}')
        return df_out, 1

    # Header document data    
    t_filein = [str(file_input.name)]
    
    tag_fattura_b2b = './/FatturaElettronicaHeader/DatiTrasmissione/FormatoTrasmissione/text()'
    element = tree.xpath(tag_fattura_b2b)
    for el in element:
        t_fatt_b2b.append(el)
    if t_fatt_b2b[0] != "FPR12":
        e = RuntimeError("**Error XML format file: it is NOT a b2b invoice!")
        st.exception(e)
        
    tag_prog_invio = './/FatturaElettronicaHeader/DatiTrasmissione/ProgressivoInvio/text()'
    element = tree.xpath(tag_prog_invio)
    for el in element:
        t_prog_invio.append(el)       
    tag_piva_mitt = './/FatturaElettronicaHeader/CedentePrestatore/DatiAnagrafici/IdFiscaleIVA/IdCodice/text()'
    element = tree.xpath(tag_piva_mitt)
    for el in element:
        t_piva_mitt.append(el) 
    tag_desc_mitt = './/FatturaElettronicaHeader/CedentePrestatore/DatiAnagrafici/Anagrafica/Denominazione/text()'
    element = tree.xpath(tag_desc_mitt)
    for el in element:
        t_desc_mitt.append(el)
    tag_num_doc = './/FatturaElettronicaBody/DatiGenerali/DatiGeneraliDocumento/Numero/text()'
    element = tree.xpath(tag_num_doc)
    for el in element:
        t_num_doc.append(el)
    tag_data_doc = './/FatturaElettronicaBody/DatiGenerali/DatiGeneraliDocumento/Data/text()'
    element = tree.xpath(tag_data_doc)
    for el in element:
        t_data_doc.append(el)
    tag_importo_doc = './/FatturaElettronicaBody/DatiGenerali/DatiGeneraliDocumento/ImportoTotaleDocumento/text()'
    element = tree.xpath(tag_importo_doc)
    for el in element:
        t_importo_doc.append(el)    
    tag_causale = './/FatturaElettronicaBody/DatiGenerali/DatiGeneraliDocumento/Causale/text()'
    element = tree.xpath(tag_causale)
    for el in element:
        t_causale.append(el)
    if len(element) == 0:
        t_causale.append(' ')
    # Position document data
    tag_nr_linea = './/FatturaElettronicaBody/DatiBeniServizi/DettaglioLinee/NumeroLinea/text()'
    element = tree.xpath(tag_nr_linea)
    for el in element:
        d_nr_linea.append(el)

    tag_codart = './/FatturaElettronicaBody/DatiBeniServizi/DettaglioLinee/CodiceArticolo/CodiceValore/text()'
    element = tree.xpath(tag_codart)
    for el in element:
        d_codart.append(el)

    tag_desc_linea = './/FatturaElettronicaBody/DatiBeniServizi/DettaglioLinee/Descrizione/text()'
    element = tree.xpath(tag_desc_linea)
    for el in element:
        d_desc_linea.append(el)

    tag_qta = './/FatturaElettronicaBody/DatiBeniServizi/DettaglioLinee/Quantita/text()'
    element = tree.xpath(tag_qta)
    for el in element:
        d_qta.append(el)

    tag_um = './/FatturaElettronicaBody/DatiBeniServizi/DettaglioLinee/UnitaMisura/text()'
    element = tree.xpath(tag_um)
    for el in element:
        d_um.append(el)

    tag_przunit = './/FatturaElettronicaBody/DatiBeniServizi/DettaglioLinee/PrezzoUnitario/text()'
    element = tree.xpath(tag_przunit)
    for el in element:
        d_przunit.append(el)

    tag_prezzo_tot = './/FatturaElettronicaBody/DatiBeniServizi/DettaglioLinee/PrezzoTotale/text()'
    element = tree.xpath(tag_prezzo_tot)
    for el in element:
        d_prezzo_tot.append(el)

    tag_tiponota = './/FatturaElettronicaBody/DatiBeniServizi/DettaglioLinee/AltriDatiGestionali/TipoDato/text()'
    element = tree.xpath(tag_tiponota)
    for el in element:
        d_tiponota.append(el)

    tag_descnota = './/FatturaElettronicaBody/DatiBeniServizi/DettaglioLinee/AltriDatiGestionali/RiferimentoTesto/text()'
    element = tree.xpath(tag_descnota)
    for el in element:
        d_descnota.append(el)

    allegati = dict()
    for i in range(len(d_tiponota)):
      nr_disegno = " "
      if d_tiponota[i] == "DISEGNO":
        allegati[i] = d_tiponota[i]
    for i in allegati.keys():
      nr_disegno = d_descnota[i]
      d_nrdisegno.append(nr_disegno)
    allegati = dict()
    for i in range(len(d_tiponota)):
      nr_disegno = " "
      if d_tiponota[i] == "N01":
        allegati[i] = d_tiponota[i]
    for i in allegati.keys():
      rifdoc = d_descnota[i]
      d_rifdoc.append(rifdoc)

    tag_bolli = "RIMB.SPESE BOLLI        "
    idx_bolli = d_desc_linea.index(tag_bolli)
    if idx_bolli != -1:
#      d_nr_linea.insert(idx_bolli,"**")
      d_codart.insert(idx_bolli,"**")
      d_um.insert(idx_bolli,"**")
      d_nrdisegno.insert(idx_bolli,'**')
      d_rifdoc.insert(idx_bolli,'**')

    # Adjust lists size for having the same number of elements   
    nr_lines = len(d_nr_linea)
    if nr_lines != 0:
        t_filein = t_filein * nr_lines            
        t_prog_invio = t_prog_invio * nr_lines
        t_piva_mitt = t_piva_mitt * nr_lines
        if len(t_desc_mitt) == 0:
            t_desc_mitt = [' '] 
        t_desc_mitt = t_desc_mitt * nr_lines
        t_num_doc = t_num_doc * nr_lines
        t_data_doc = t_data_doc * nr_lines
        t_importo_doc = t_importo_doc * nr_lines
        if len(t_causale) == 0:
            t_causale = [' ']    
        t_causale = t_causale * nr_lines

    # Create the dataframe
    df_out = pd.DataFrame({'T_filein': t_filein,
#                           'T_prog_invio': t_prog_invio,
                           'T_piva_mitt': t_piva_mitt,
                           'T_desc_mitt': t_desc_mitt,
                           'T_num_doc': t_num_doc,
                           'T_data_doc': t_data_doc,
                           'T_importo_doc': t_importo_doc,
                           'T_causale': t_causale,
                           'P_nr_linea': d_nr_linea,
                           'P_codart': d_codart,
                           'P_desc_linea': d_desc_linea,
                           'P_qta': d_qta,
                           'P_um': d_um,
                           'P_przunit': d_przunit,
                           'P_prezzo_tot': d_prezzo_tot,
                           'P_nrdisegno': d_nrdisegno,
                           'P_rifdoc': d_rifdoc,
                           })
    # Convert some columns into float data type
#    df_out['T_data_doc'] = df_out['T_data_doc'].astype('datetime64[ns]')    
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


