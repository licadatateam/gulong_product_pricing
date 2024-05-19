# -*- coding: utf-8 -*-
"""
Created on Wed May  8 22:10:35 2024

@author: carlo
"""
import os, sys
import json
import numpy as np
import pandas as pd
from datetime import datetime as dt

import main_pricing_2
import st_wrapper_catalog

import streamlit as st
from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode
from st_aggrid.grid_options_builder import GridOptionsBuilder

# load google service account
try:
    creds = st.secrets['secrets']
except:
    with open('secrets.json') as file:
        creds = json.load(file)

# configure working directory
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
output_path = os.path.abspath(os.path.dirname(__file__))
os.chdir(output_path)

@st.cache_data
def to_float(num : (int, float, str)):
    '''
    Check if value is convertible to float
    
    Parameters:
    -----------
        - num : int, str, float
    
    Returns:
    -------
        - bool : True or False
    '''
    try:
        float(num)
        return True
    except ValueError:
        return False


@st.cache_data
def acquire_data():
    '''
    Wrapping function of acquire_data to apply caching
    '''
    return main_pricing_2.acquire_data()

@st.cache_data
def implement_sale(df : pd.DataFrame, 
                   sale_tag : str, 
                   promo : str, 
                   srp : str) -> pd.DataFrame:
    '''
    Applies SRP to non-sale items
    
    Parameters:
    -----------
        df : pd.DataFrame
            dataframe to modify (df_final from acquire_data())
        sale_tag : str
            column name of sale tag
        promo : str
            column name of Gulong PH promo price (GulongPH)
        srp : str
            column name of Gulong PH srp (GulongPH_slashed)
    
    Returns:
    --------
        - df : pd.DataFrame
    
    '''
    df.loc[df[sale_tag]==0, promo] = df.loc[df[sale_tag]==0, srp]
    return df

def update():
    '''
    Resets cache data and runtime
    '''
    st.cache_data.clear()
    del st.session_state['adjusted']
    del st.session_state['GP_15']
    del st.session_state['GP_20']
    del st.session_state['GP_20_']
    st.experimental_rerun()

def set_session_state(updated_at : str = None):
    '''
    Initializes session state
    
    Parameters:
    -----------
        None
    Returns:
    --------
        None
    
    '''
    
    if 'updated_at' not in st.session_state:
        if updated_at is None:
            st.session_state['updated_at'] = dt.today().date().strftime('%Y-%m-%d')
        else:
            st.session_state['updated_at'] = updated_at

    if 'GP_15' not in st.session_state:
        st.session_state['GP_15'] = 15
    if 'GP_20' not in st.session_state:
        st.session_state['GP_20'] = 5
    if 'GP_20_' not in st.session_state:
        st.session_state['GP_20_']= 3
    if 'd_b2b' not in st.session_state:
        st.session_state['d_b2b'] = 25
    if 'd_affiliate' not in st.session_state:
        st.session_state['d_affiliate'] = 27
    if 'd_marketplace' not in st.session_state:
        st.session_state['d_marketplace'] = 25
    
    if 'reload_data' not in st.session_state:
        st.session_state['reload_data'] = False
    
    if 'adjusted' not in st.session_state:
        st.session_state['adjusted'] = False
        
    if 'updated_at' not in st.session_state:
        update()

def quick_calculator():
    '''
    Sidebar tool for quick calculations around selling price, supplier price
    and GP
    
    Parameters:
    ----------
        None.
    
    Returns:
    --------
        None.
    
    '''
    find_value = st.radio("Find:", ('Selling Price', 
                                    'Supplier Price', 
                                    'GP(%)'))
    q1,q2 = st.columns([1,1])
    if find_value =='Selling Price':     
        with q1:
            qsp = st.text_input('Supplier Price:', 
                                value="1000.00")
        with q2:
            qgp = st.text_input('GP: (%)', 
                                value="30.00")
            if to_float(qgp) and to_float(qsp):
                value = main_pricing_2.consider_GP(float(qsp),
                                                   float(qgp))
            else:
                value = "Input Error"
                
    if find_value =='Supplier Price':       
        with q1:
            qsp = st.text_input('Selling Price:', 
                                value="1000.00")
        with q2:
            qgp = st.text_input('GP (%):', 
                                value="30.00")
            
            if to_float(qgp) and to_float(qsp):
                value = round(float(qsp)/(1+float(qgp)/100),)
            else:
                value = "Input Error"
                
    if find_value == 'GP(%)':
        with q1:
            qsp = st.text_input('Selling Price:', 
                                value="1500.00")
        with q2:
            qsupp = st.text_input('Supplier Price:', 
                                  value="1000.00")
            
            if (to_float(qsupp) and to_float(qsp)):
                if float(qsp)==0:
                    value = "Input Error"
                else:
                    value = main_pricing_2.get_GP(qsupp, qsp)
            else:
                value = "Input Error"
    # show
    st.metric(find_value, value)
    
def rename_tiers() -> dict:
    '''
    Sidebar option to rename tiers
    
    Parameters:
    -----------
        None
    
    Returns:
    --------
        - tier_names : dict
    
    '''
    
    t1_name = st.text_input('Tier 1 name:', 'Website Slashed Price Test')
    t2_name = st.text_input('Tier 2 name:', 'Website Prices Test')
    t3_name = st.text_input('Tier 3 name:', 'B2B Test')
    t4_name = st.text_input('Tier 4 name:', 'Marketplace Test')
    t5_name = st.text_input('Tier 5 name:', 'Affiliates Test')
    tier_names = {'tier1' : t1_name,
             'tier2' : t2_name,
             'tier3' : t3_name,
             'tier4' : t4_name,
             'tier5' : t5_name}
    return tier_names

@st.cache_data
def adjust_wrt_gogulong(df,
                        GP_15,
                        GP_20a,
                        GP_20b,
                        b2b,
                        affiliate,
                        marketplace):
    '''
    Wrapping function of adjust_wrt_gogulong to apply caching
    '''
    return main_pricing_2.adjust_wrt_gogulong(df,
                            GP_15,
                            GP_20a,
                            GP_20b,
                            b2b,
                            affiliate,
                            marketplace)

def build_grid(df_show : pd.DataFrame):
    '''
    Configures GridOptionsBuilder
    
    Parameters:
    -----------
        - df_show : pd.DataFrame
    
    Returns:
        - response : AgGrid object
    
    '''
    gb = GridOptionsBuilder.from_dataframe(df_show)
    gb.configure_columns(autoSizeAllColumns = True)
    gb.configure_default_column(enablePivot=False, 
                                enableValue=False, 
                                enableRowGroup=False, 
                                editable = True)
    gb.configure_column('sku_name', headerCheckboxSelection = True,
                        pinned = True)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_side_bar()  
    gridOptions = gb.build()
    
    # show table
    response = AgGrid(df_show,
        #theme = 'light',
        gridOptions=gridOptions,
        height = 300,
        #width = '100%',
        editable=True,
        allow_unsafe_jscode=True,
        reload_data = st.session_state['reload_data'],
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=False)
    
    # reset
    st.session_state['reload_data'] = False
    
    return response

def convert_df(df):
     # IMPORTANT: Cache the conversion to prevent computation on every rerun
     return df.to_csv().encode('utf-8')

def highlight_promo(xa : pd.DataFrame):
    df1 = pd.DataFrame('background-color: ', index = xa.index, 
                       columns = xa.columns)
    col_eval = ['GulongPH','GulongPH_slashed','b2b','marketplace']
    highlight_competitor = '#ffffb3'
    temp_list = list(col_tier)
    col_eval = col_eval+temp_list
    for column in col_eval:
        c = xa['supplier_max_price'] > xa[column]
        df1['supplier_max_price']= np.where(c, 'background-color: {}'.format('pink'), df1['supplier_max_price'])
        df1[column]= np.where(c, 'background-color: {}'.format('pink'), df1[column])
    if 'selection_max_price' in xa.columns.tolist():
        c = xa['selection_max_price']<xa['supplier_max_price']
        df1['selection_max_price'] = np.where(c, 'background-color: {}'.format('lightgreen'), df1['selection_max_price'])
    if 'GoGulong' in xa.columns.tolist():
        
        c = xa['GulongPH']>xa['GoGulong']
        df1['GulongPH'] = np.where(c, 'background-color: {}'.format(highlight_competitor), df1['GulongPH'])
        df1['GoGulong'] = np.where(c, 'background-color: {}'.format(highlight_competitor), df1['GoGulong'])
    if 'TireManila' in xa.columns.tolist():
        c = xa['GulongPH']>xa['TireManila']
        df1['TireManila'] = np.where(c, 'background-color: {}'.format(highlight_competitor), df1['TireManila'])
        df1['GulongPH'] = np.where(c, 'background-color: {}'.format(highlight_competitor), df1['GulongPH'])
    return df1

if __name__ == "__main__":
    
    ## Sidebar Tool : Quick Calculator
    qc_expander = st.sidebar.expander("Quick Calculator", expanded = False)
    with qc_expander:
        quick_calculator()
    
    # Sidebar Tool : Rename Tiers
    t_name= st.sidebar.expander("Rename Tiers:", expanded = False)
    with t_name:
        tier_names = rename_tiers()
        
    # Load data
    # keys : df_final, cols_option, df_competitor, last_update
    data_dict = acquire_data()
    
    # initialize session state
    set_session_state(updated_at = data_dict['backend_last_update'])
    
    # displays update status of data displayed
    upd_btn, upd_data = st.sidebar.columns([2,3])
    with upd_btn:
        help_note = 'Acquires results of query from backend and resets program'
        if st.button('Update Data', help = help_note):
            update()
    with upd_data:
        st.caption(f'Gulong PH data last updated on {data_dict["backend_last_update"]}')
        comp_update = str(data_dict['comp_last_update']).replace('/', '-')
        st.caption(f'Competitor data last updated on {comp_update}.')
    
    st.sidebar.markdown("""---""")
    
    # auto-adjust values toggle
    auto_adj_btn, auto_adj_txt = st.sidebar.columns([2,3])
    with auto_adj_btn:
        is_adjusted = st.checkbox('Auto-adjust')
    with auto_adj_txt:
        st.caption('Automatically adjusts data based on GoGulong values')
    if is_adjusted:
        st.session_state['adjusted'] = True
    else:
        st.session_state['adjusted'] = False
    
    if st.session_state['adjusted']:
        # adjust srp price to non-sale gulong items
        df_final_ = implement_sale(data_dict['df_final'], 
                                   'sale_tag', 
                                   'GulongPH', 
                                   'GulongPH_slashed').drop(columns= 'sale_tag')
        
        df_final_ = df_final_.set_index('model')
        # adjust gulong prices with respect to gogulong
        df_temp_adjust = adjust_wrt_gogulong(df_final_,
                                             st.session_state['GP_15'],
                                             st.session_state['GP_20'],
                                             st.session_state['GP_20_'],
                                             st.session_state['d_b2b'],
                                             st.session_state['d_affiliate'],
                                             st.session_state['d_marketplace'])
        # update values
        df_final_.update(df_temp_adjust[['GulongPH',
                                        'GulongPH_slashed',
                                        'b2b',
                                        'affiliate',
                                        'marketplace']], 
                        overwrite = True)
        df_final = df_final_.reset_index()
    else:
        df_final = data_dict['df_final'].copy()

    # edit mode
    edit_mode = st.sidebar.selectbox('Mode', 
                                     options = ('Automated',
                                                'Manual'),
                                     index = 1)
    
    check_adjusted = st.sidebar.checkbox('Show adjusted prices only', 
                                         value = False)
    
    # supplier files upload
    if 'df_supplier' not in st.session_state:
        st.session_state['df_supplier'] = None
    
    with st.expander('Supplier Files Upload', expanded = False):
        df_supplier = st_wrapper_catalog.main()
        
        if df_supplier is not None:
            st.session_state['df_supplier'] = df_supplier
            
        else:
            df_supplier = st.session_state['df_supplier']
        
        if st.session_state['df_supplier'] is not None:
            st.write(st.session_state['df_supplier'])
    
    st.markdown("---")
    
    # Manual edit mode
    if edit_mode == 'Manual':
        st.header("Data Review")
        
        with st.expander('Include/remove columns in list:'):
            beta_multiselect = st.container()
            check_all = st.checkbox('Select all', value=False)
            # list of default columns to show
            def_list = list(data_dict['cols_option']) if check_all else []
            # if supplier files upload, add suppliers included
            if df_supplier is not None:
                def_list.extend(list(df_supplier.supplier.unique()))
                
            selected_cols = beta_multiselect.multiselect('Included columns in table:',
                                           options = data_dict['cols_option'],
                                           default = def_list)

        
        df_show = df_final.merge(data_dict['df_final'][['model', 'GulongPH']], 
                                       how = 'left',
                                       on = 'model', 
                                       suffixes=('', '_backend'))
        
        # merge supplier df if uploaded files
        if df_supplier is not None:
            qty_cols = [f'qty_{s}' for s in list(df_supplier.supplier.unique())]
            price_cols = [f'price_{s}' for s in list(df_supplier.supplier.unique())]
            supplier_cols = ['similar_pattern', 'correct_specs',
                             'brand'] + qty_cols + price_cols
            
            df_show = df_show.merge(df_supplier[supplier_cols],
                                    how = 'left',
                                    left_on = ['pattern', 'dimensions', 
                                               'make'],
                                    right_on = ['similar_pattern', 'correct_specs', 
                                                'brand'],
                                    suffixes = ('', '_')).drop_duplicates()
            
            selected_cols.extend(qty_cols + price_cols)
        
        if check_adjusted:
            df_show = df_show.loc[df_show['GulongPH']
                                  != df_show['GulongPH_backend']]
        
        # TODO: preorder
        
        
        # default table columns
        cols = ['model_','model','make', 'pattern', 'dimensions', 'supplier_max_price',
                '3+1_promo_per_tire_GP25','GulongPH','GulongPH_slashed',
                'b2b','marketplace', 'GoGulong', 'TireManila', 'PartsPro',
                'qty_tiremanila', 'year']
        
        # TODO: reorder columns (qty and price)
        
        if len(selected_cols) > 0:
            # add selected cols to display
            cols.extend(selected_cols)
        
        # final dataframe to show
        df_show = df_show.dropna(how = 'all', 
                                        subset = cols,
                                        axis=0).replace(np.nan,'')
        
        df_show = df_show[cols].drop(columns='model').rename(
                                                    columns={'model_': 'sku_name'})
        
        
        
        
        st.write("""Select the SKUs that would be considered for the computations.
                 Feel free to filter the _make_ and _model_ that would be shown. 
                 You may also select/deselect columns.""")
                 
        reset_btn, reset_capt = st.sidebar.columns([1, 1])
        with reset_btn:
            if st.button('Reset changes'):
                st.session_state['reload_data'] = True
        with reset_capt:
            st.caption('Resets the edits done in the table.')
        
        

        # build and show table
        response = build_grid(df_show)
        
        AG1, AG2 = st.columns([3,2])
        with AG1:
            st.write(f"Results: {len(df_show)} entries")
        with AG2:
            st.download_button(label="📥 Download this table.",
                                data=convert_df(pd.DataFrame.from_dict(response['data'])),
                                file_name='grid_table.csv',
                                mime='text/csv')
        
    if edit_mode == 'Automated':
        pass
